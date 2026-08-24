import pulp
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

class BatteryOptimizer:
    """
    Mixed-Integer Linear Programming (MILP) model to optimize 
    Virtual Power Plant (VPP) dispatch scheduling for maximum P&L,
    incorporating real-world thermodynamic efficiency and cycle aging.
    """
    def __init__(self, prices: list, max_capacity: float = 100.0, max_rate: float = 25.0, efficiency: float = 0.9):
        self.prices = prices
        self.T = len(prices)
        self.max_capacity = max_capacity
        self.max_rate = max_rate
        self.efficiency = efficiency  # 90% round-trip efficiency
        self.degradation_cost = 5.0   # €5/MWh physical wear-and-tear penalty
        
        # Initialize the LP Maximization Problem
        self.model = pulp.LpProblem("VPP_Battery_Dispatch", pulp.LpMaximize)
        
    def build_model(self):
        """Constructs the decision variables, objective function, and physical constraints."""
        # 1. Decision Variables (Bounded by max physical flow rates)
        self.charge = pulp.LpVariable.dicts("Charge", range(self.T), lowBound=0, upBound=self.max_rate)
        self.discharge = pulp.LpVariable.dicts("Discharge", range(self.T), lowBound=0, upBound=self.max_rate)
        self.soc = pulp.LpVariable.dicts("StateOfCharge", range(self.T), lowBound=0, upBound=self.max_capacity)
        
        # 2. Objective Function: Maximize Revenue MINUS Degradation Costs
        self.model += pulp.lpSum([
            (self.prices[t] * (self.discharge[t] - self.charge[t])) - 
            (self.degradation_cost * (self.discharge[t] + self.charge[t])) 
            for t in range(self.T)
        ])
        
        # 3. Physical Constraints (Energy Balance with Efficiency Penalty)
        for t in range(self.T):
            if t == 0:
                # Initial state: Battery starts empty. Charging loses energy to heat.
                self.model += self.soc[t] == (self.charge[t] * self.efficiency) - self.discharge[t]
            else:
                # Continuous state: Current SOC = Previous SOC + Net Charge - Discharge
                self.model += self.soc[t] == self.soc[t-1] + (self.charge[t] * self.efficiency) - self.discharge[t]

    def solve(self) -> pd.DataFrame:
        """Executes the optimization solver and formats the resulting schedule."""
        self.build_model()
        status = self.model.solve(pulp.PULP_CBC_CMD(msg=False))
        
        if pulp.LpStatus[status] == 'Optimal':
            print(f"Optimal Schedule Found! Total Simulated P&L: €{pulp.value(self.model.objective):.2f}")
            
            # Extract the mathematically optimal schedule
            schedule = pd.DataFrame({
                "Hour": range(self.T),
                "Price (€/MWh)": self.prices,
                "Charge (MW)": [self.charge[t].varValue for t in range(self.T)],
                "Discharge (MW)": [self.discharge[t].varValue for t in range(self.T)],
                "State of Charge (MWh)": [self.soc[t].varValue for t in range(self.T)]
            })
            return schedule
        else:
            print("Optimization Failed: No feasible physical solution.")
            return pd.DataFrame()

    def plot_dispatch(self, df: pd.DataFrame):
        """Generates a dual-axis stack chart for the README visual analytics."""
        fig, ax1 = plt.subplots(figsize=(12, 6))
        ax2 = ax1.twinx()
        
        # Overlay the volatile price line
        ax1.plot(df["Hour"], df["Price (€/MWh)"], color="black", label="Price", marker="o")
        ax1.set_ylabel("Price (€/MWh)", fontweight="bold")
        
        # Plot the physical flow state
        ax2.bar(df["Hour"], df["Discharge (MW)"], color="green", alpha=0.6, label="Discharge (Sell)")
        ax2.bar(df["Hour"], -df["Charge (MW)"], color="red", alpha=0.6, label="Charge (Buy)")
        ax2.set_ylabel("Power Flow (MW)", fontweight="bold")
        
        plt.title("Optimized VPP Dispatch Schedule")
        
        # Combine legends
        lines_1, labels_1 = ax1.get_legend_handles_labels()
        lines_2, labels_2 = ax2.get_legend_handles_labels()
        ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc="upper right", bbox_to_anchor=(0.95, 0.95))
        
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    # Simulate 24 hours of volatile day-ahead electricity prices
    np.random.seed(42)
    mock_prices = np.random.uniform(20, 150, 24)
    
    # Injecting real-world market dynamics
    mock_prices[17:20] = [300, 450, 280]  # Evening demand peak (Dunkelflaute)
    mock_prices[3:6] = [10, -5, 15]       # Nighttime trough (Negative pricing due to excess wind)
    
    # Initialize and solve
    optimizer = BatteryOptimizer(prices=mock_prices.tolist())
    dispatch_schedule = optimizer.solve()
    
    if not dispatch_schedule.empty:
        print("\n--- 24-Hour Battery Dispatch Schedule (First 10 Hours) ---")
        print(dispatch_schedule.head(10))
        
        # Generate the visual for the README
        print("\nGenerating Dispatch Stack Chart...")
        optimizer.plot_dispatch(dispatch_schedule)