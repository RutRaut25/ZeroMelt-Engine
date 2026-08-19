from typing import List
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from app.schemas import DarkStoreHub, Order, Courier, OptimizationResult, CourierRoute, RouteStop
from app.graph import build_spatial_matrices
from app.decay import calculate_quality, compute_max_safe_transit_time


class ColdChainVRPTSolver:
    def __init__(
        self,
        hub: DarkStoreHub,
        orders: List[Order],
        couriers: List[Courier],
        ambient_temp_c: float = 34.0,
    ):
        self.hub = hub
        self.orders = orders
        self.couriers = couriers
        self.ambient_temp_c = ambient_temp_c
        
        self.dist_matrix, self.time_matrix, self.coordinates = build_spatial_matrices(hub, orders)
        self.num_nodes = len(self.coordinates)
        self.num_vehicles = len(couriers)
        self.depot = 0

    def solve(self) -> OptimizationResult:
        manager = pywrapcp.RoutingIndexManager(self.num_nodes, self.num_vehicles, self.depot)
        routing = pywrapcp.RoutingModel(manager)

        # 1. Distance Cost Callback
        def distance_callback(from_index: int, to_index: int) -> int:
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return self.dist_matrix[from_node][to_node]

        transit_callback_idx = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_idx)

        # 2. Payload Capacity Dimension
        weights = [0] + [sum(item.weight_kg for item in o.items) for o in self.orders]

        def demand_callback(from_index: int) -> int:
            node = manager.IndexToNode(from_index)
            return int(weights[node] * 100)  # Convert kg to integer scale

        demand_callback_idx = routing.RegisterUnaryTransitCallback(demand_callback)
        max_capacities = [int(c.max_payload_kg * 100) for c in self.couriers]
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_idx,
            0,  # null capacity slack
            max_capacities,
            True,  # start cumulative load at zero
            "Capacity",
        )

        # 3. Time Windows & Perishable Decay Dimension
        def time_callback(from_index: int, to_index: int) -> int:
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return self.time_matrix[from_node][to_node]

        time_callback_idx = routing.RegisterTransitCallback(time_callback)
        horizon_minutes = 60  # max 1-hour shift window
        routing.AddDimension(
            time_callback_idx,
            horizon_minutes,
            horizon_minutes,
            False,
            "Time",
        )
        time_dimension = routing.GetDimensionOrDie("Time")

        # Apply dynamic time windows based on decay kinetics
        for order_idx, order in enumerate(self.orders):
            node = order_idx + 1
            index = manager.NodeToIndex(node)
            
            # Find earliest spoilage deadline for items in the bag
            cold_chain_deadlines = [
                compute_max_safe_transit_time(it, self.ambient_temp_c, order.min_quality_threshold)
                for it in order.items
            ]
            most_urgent_spoilage_min = min(cold_chain_deadlines) if cold_chain_deadlines else order.latest_minute
            
            effective_deadline = int(min(order.latest_minute, most_urgent_spoilage_min))
            earliest_start = int(order.earliest_minute)
            
            time_dimension.CumulVar(index).SetRange(earliest_start, max(earliest_start, effective_deadline))

        # Allow skipping infeasible orders under high penalty
        for node in range(1, self.num_nodes):
            routing.AddDisjunction([manager.NodeToIndex(node)], 100_000)

        # Solver Strategy Parameters
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.seconds = 2

        solution = routing.SolveWithParameters(search_parameters)

        if not solution:
            return OptimizationResult(
                status="INFEASIBLE",
                routes=[],
                unassigned_orders=[o.order_id for o in self.orders],
                total_distance_km=0.0,
                fleet_spoilage_rate_pct=100.0,
                ambient_temp_celsius=self.ambient_temp_c,
            )

        return self._build_solution_response(manager, routing, solution, time_dimension)

    def _build_solution_response(
        self, manager, routing, solution, time_dimension
    ) -> OptimizationResult:
        routes: List[CourierRoute] = []
        assigned_nodes = set()
        total_dist_meters = 0
        total_items_delivered = 0
        total_spoiled_items = 0

        for vehicle_id in range(self.num_vehicles):
            index = routing.Start(vehicle_id)
            stops: List[RouteStop] = []
            route_dist = 0
            route_load = 0.0

            while not routing.IsEnd(index):
                node = manager.IndexToNode(index)
                time_var = time_dimension.CumulVar(index)
                arrival_min = solution.Min(time_var)
                departure_min = solution.Max(time_var)

                if node != 0:
                    assigned_nodes.add(node)
                    order = self.orders[node - 1]
                    route_load += sum(it.weight_kg for it in order.items)
                    
                    qualities = {}
                    is_safe = True
                    for it in order.items:
                        q = calculate_quality(it, arrival_min, self.ambient_temp_c)
                        qualities[it.name] = q
                        total_items_delivered += 1
                        if q < order.min_quality_threshold:
                            is_safe = False
                            total_spoiled_items += 1

                    stops.append(
                        RouteStop(
                            order_id=order.order_id,
                            latitude=order.latitude,
                            longitude=order.longitude,
                            arrival_minute=float(arrival_min),
                            departure_minute=float(departure_min),
                            quality_indices=qualities,
                            is_safe=is_safe,
                        )
                    )

                prev_index = index
                index = solution.Value(routing.NextVar(index))
                route_dist += routing.GetArcCostForVehicle(prev_index, index, vehicle_id)

            if stops:
                courier = self.couriers[vehicle_id]
                total_duration = stops[-1].departure_minute if stops else 0.0
                routes.append(
                    CourierRoute(
                        courier_id=courier.courier_id,
                        courier_name=courier.name,
                        stops=stops,
                        total_distance_km=round(route_dist / 1000.0, 2),
                        total_duration_minutes=round(total_duration, 1),
                        total_load_kg=round(route_load, 2),
                        spoilage_count=sum(1 for s in stops if not s.is_safe),
                    )
                )
                total_dist_meters += route_dist

        all_order_indices = set(range(1, self.num_nodes))
        unassigned_indices = all_order_indices - assigned_nodes
        unassigned_ids = [self.orders[i - 1].order_id for i in unassigned_indices]

        spoilage_pct = (
            (total_spoiled_items / total_items_delivered * 100) if total_items_delivered > 0 else 0.0
        )

        return OptimizationResult(
            status="OPTIMAL" if len(unassigned_ids) == 0 else "PARTIAL",
            routes=routes,
            unassigned_orders=unassigned_ids,
            total_distance_km=round(total_dist_meters / 1000.0, 2),
            fleet_spoilage_rate_pct=round(spoilage_pct, 2),
            ambient_temp_celsius=self.ambient_temp_c,
        )