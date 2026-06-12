"""
Drift Dashboard - Real-time Acceptance Rate Trend Tracking

Monitors:
1. Acceptance rate trends over time
2. Drift detection (when acceptance rate degrades)
3. Confidence vs acceptance correlation
4. Early warning system for quality degradation
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from dataclasses import dataclass
import math


@dataclass
class DriftAlert:
    """Alert for detected drift"""
    alert_time: str
    metric: str  # acceptance_rate, rejection_rate, etc
    current_value: float
    expected_value: float
    threshold: float
    severity: str  # "warning", "critical"
    message: str


class DriftDetector:
    """Detects quality drift in acceptance rates"""
    
    def __init__(self, window_size: int = 20, threshold_std_devs: float = 2.0):
        """
        Initialize drift detector
        window_size: number of tickets to analyze per window
        threshold_std_devs: how many standard deviations indicates drift
        """
        self.window_size = window_size
        self.threshold_std_devs = threshold_std_devs
        self.alerts: List[DriftAlert] = []
    
    def analyze_acceptance_drift(self, feedback_data: List[Dict]) -> Dict:
        """Analyze acceptance rate drift over time"""
        
        # Create sliding windows
        windows = []
        for i in range(0, len(feedback_data), self.window_size):
            window_data = feedback_data[i:i + self.window_size]
            if not window_data:
                continue
            
            # Calculate metrics for this window
            acceptance_rate = sum(1 for f in window_data if f.get("feedback") == "accepted") / len(window_data)
            edit_rate = sum(1 for f in window_data if f.get("feedback") == "edited") / len(window_data)
            rejection_rate = sum(1 for f in window_data if f.get("feedback") == "rejected") / len(window_data)
            avg_quality = sum(f.get("quality", 0) for f in window_data) / len(window_data)
            avg_confidence = sum(f.get("confidence", 0) for f in window_data) / len(window_data)
            
            windows.append({
                "window_id": len(windows),
                "size": len(window_data),
                "acceptance_rate": acceptance_rate,
                "edit_rate": edit_rate,
                "rejection_rate": rejection_rate,
                "avg_quality": avg_quality,
                "avg_confidence": avg_confidence,
            })
        
        # Calculate statistics across windows
        if len(windows) < 2:
            return {"windows": windows, "alerts": [], "drift_detected": False}
        
        acceptance_rates = [w["acceptance_rate"] for w in windows]
        mean_acceptance = sum(acceptance_rates) / len(acceptance_rates)
        variance = sum((x - mean_acceptance) ** 2 for x in acceptance_rates) / len(acceptance_rates)
        std_dev = math.sqrt(variance)
        
        # Detect drift using statistical process control
        alerts = self._detect_drift_anomalies(windows, mean_acceptance, std_dev)
        
        return {
            "total_windows": len(windows),
            "windows": windows,
            "statistics": {
                "mean_acceptance": mean_acceptance,
                "std_dev_acceptance": std_dev,
                "min_acceptance": min(acceptance_rates),
                "max_acceptance": max(acceptance_rates),
                "trend": self._calculate_trend(acceptance_rates),
            },
            "alerts": [
                {
                    "time": a.alert_time,
                    "metric": a.metric,
                    "current": a.current_value,
                    "expected": a.expected_value,
                    "severity": a.severity,
                    "message": a.message,
                }
                for a in alerts
            ],
            "drift_detected": len(alerts) > 0,
        }
    
    def _detect_drift_anomalies(self, windows: List[Dict], mean: float, std_dev: float) -> List[DriftAlert]:
        """Detect anomalies using statistical process control"""
        alerts = []
        
        for i, window in enumerate(windows):
            acceptance = window["acceptance_rate"]
            rejection = window["rejection_rate"]
            
            # Check for acceptance rate drift
            z_score = (acceptance - mean) / std_dev if std_dev > 0 else 0
            
            if z_score < -self.threshold_std_devs:
                # Significant drop in acceptance
                severity = "critical" if z_score < -3.0 else "warning"
                alerts.append(DriftAlert(
                    alert_time=datetime.now().isoformat(),
                    metric="acceptance_rate",
                    current_value=acceptance,
                    expected_value=mean,
                    threshold=mean - (self.threshold_std_devs * std_dev),
                    severity=severity,
                    message=f"Window {i}: Acceptance rate dropped to {acceptance:.1%} (expected ~{mean:.1%}). "
                           f"Z-score: {z_score:.2f}. System quality may be degrading."
                ))
            
            # Check for high rejection rate
            if rejection > 0.15:
                alerts.append(DriftAlert(
                    alert_time=datetime.now().isoformat(),
                    metric="rejection_rate",
                    current_value=rejection,
                    expected_value=0.10,
                    threshold=0.15,
                    severity="warning",
                    message=f"Window {i}: Rejection rate elevated at {rejection:.1%}. "
                           f"Quality issues may require attention."
                ))
        
        return alerts
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate if trend is improving or degrading"""
        if len(values) < 2:
            return "neutral"
        
        first_half = sum(values[:len(values)//2]) / (len(values)//2)
        second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        if second_half > first_half + 0.05:
            return "improving"
        elif second_half < first_half - 0.05:
            return "degrading"
        else:
            return "stable"


class AcceptanceRateDashboard:
    """Dashboard for acceptance rate trends"""
    
    def __init__(self):
        self.drift_detector = DriftDetector(window_size=20)
        self.historical_data = []
    
    def load_feedback_data(self, feedback_filepath: str = "data/feedback.json", tickets_filepath: str = "data/tickets.json"):
        """Load actual feedback data from files"""
        try:
            # Load feedback data
            with open(feedback_filepath, "r") as f:
                feedback_data = json.load(f)
            
            # Load tickets data
            with open(tickets_filepath, "r") as f:
                tickets_data = json.load(f)
            
            # Combine feedback with ticket info
            combined_data = []
            for ticket_id, ticket_info in tickets_data.items():
                feedback = feedback_data.get(ticket_id, {})
                combined_data.append({
                    "ticket_id": ticket_id,
                    "confidence": ticket_info.get("category_confidence", 0),
                    "quality": ticket_info.get("response_quality_score", 0.5),
                    "feedback": feedback.get("feedback_type", "pending"),
                })
            
            self.historical_data = combined_data
            return combined_data
        
        except FileNotFoundError as e:
            print(f"Warning: Could not load data: {e}")
            return []
    
    def generate_dashboard_data(self) -> Dict:
        """Generate all data needed for dashboard"""
        if not self.historical_data:
            self.load_feedback_data()
        
        # Handle empty data case
        if not self.historical_data:
            return {
                "dashboard_timestamp": datetime.now().isoformat(),
                "current_metrics": {
                    "acceptance_rate": 0,
                    "rejection_rate": 0,
                    "edit_rate": 0,
                    "total_tickets": 0,
                },
                "drift_analysis": {
                    "total_windows": 0,
                    "windows": [],
                    "statistics": {
                        "mean_acceptance": 0,
                        "std_dev_acceptance": 0,
                        "min_acceptance": 0,
                        "max_acceptance": 0,
                        "trend": "stable",
                    },
                    "alerts": [],
                    "drift_detected": False,
                },
                "dashboard_status": {
                    "health": "critical",
                    "trend": "stable",
                    "drift_detected": False,
                    "alerts_count": 0,
                }
            }
        
        # Run drift analysis
        drift_analysis = self.drift_detector.analyze_acceptance_drift(self.historical_data)
        
        # Calculate current metrics
        current_acceptance = sum(1 for f in self.historical_data if f.get("feedback") == "accepted") / len(self.historical_data) if self.historical_data else 0
        current_rejection = sum(1 for f in self.historical_data if f.get("feedback") == "rejected") / len(self.historical_data) if self.historical_data else 0
        current_edit = sum(1 for f in self.historical_data if f.get("feedback") == "edited") / len(self.historical_data) if self.historical_data else 0
        
        trend = drift_analysis.get("statistics", {}).get("trend", "stable")
        
        return {
            "dashboard_timestamp": datetime.now().isoformat(),
            "current_metrics": {
                "acceptance_rate": current_acceptance,
                "rejection_rate": current_rejection,
                "edit_rate": current_edit,
                "total_tickets": len(self.historical_data),
            },
            "drift_analysis": drift_analysis,
            "dashboard_status": {
                "health": "good" if current_acceptance >= 0.70 else "warning" if current_acceptance >= 0.50 else "critical",
                "trend": trend,
                "drift_detected": drift_analysis.get("drift_detected", False),
                "alerts_count": len(drift_analysis.get("alerts", [])),
            }
        }
    
    def generate_html_report(self, data: Dict) -> str:
        """Generate interactive HTML report"""
        windows = data["drift_analysis"]["windows"]
        alerts = data["drift_analysis"]["alerts"]
        stats = data["drift_analysis"]["statistics"]
        current = data["current_metrics"]
        
        # Prepare chart data
        window_ids = [str(w["window_id"]) for w in windows]
        acceptance_rates = [w["acceptance_rate"] * 100 for w in windows]
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Acceptance Rate Drift Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .dashboard {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .metric {{ display: inline-block; padding: 20px; margin: 10px; background: #f9f9f9; border-radius: 5px; min-width: 150px; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #333; }}
        .metric-label {{ font-size: 12px; color: #666; margin-top: 5px; }}
        .alert {{ padding: 10px; margin: 10px 0; border-left: 4px solid; border-radius: 3px; }}
        .alert.critical {{ background: #fee; border-color: #c33; }}
        .alert.warning {{ background: #fef3cd; border-color: #ff9800; }}
        .good {{ color: #4caf50; }}
        .warning {{ color: #ff9800; }}
        .critical {{ color: #f44336; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; margin-top: 30px; border-bottom: 2px solid #ddd; padding-bottom: 10px; }}
    </style>
</head>
<body>
    <div class="dashboard">
        <h1>📊 Acceptance Rate Drift Dashboard</h1>
        <p>Updated: {data['dashboard_timestamp']}</p>
        
        <h2>Current Status</h2>
        <div>
            <div class="metric">
                <div class="metric-value {'' if current['acceptance_rate'] >= 0.70 else 'warning' if current['acceptance_rate'] >= 0.50 else 'critical'}">
                    {current['acceptance_rate']:.1%}
                </div>
                <div class="metric-label">Acceptance Rate</div>
            </div>
            <div class="metric">
                <div class="metric-value">{current['rejection_rate']:.1%}</div>
                <div class="metric-label">Rejection Rate</div>
            </div>
            <div class="metric">
                <div class="metric-value">{current['edit_rate']:.1%}</div>
                <div class="metric-label">Edit Rate</div>
            </div>
            <div class="metric">
                <div class="metric-value">{stats['trend'].upper()}</div>
                <div class="metric-label">Trend</div>
            </div>
        </div>
        
        <h2>Acceptance Rate Trend</h2>
        <div id="trend-chart"></div>
        
        <h2>Statistics</h2>
        <div>
            <div class="metric">
                <div class="metric-value">{stats['mean_acceptance']:.1%}</div>
                <div class="metric-label">Mean Acceptance</div>
            </div>
            <div class="metric">
                <div class="metric-value">±{stats['std_dev_acceptance']:.1%}</div>
                <div class="metric-label">Std Dev</div>
            </div>
            <div class="metric">
                <div class="metric-value">{stats['min_acceptance']:.1%} - {stats['max_acceptance']:.1%}</div>
                <div class="metric-label">Range</div>
            </div>
        </div>
        
        <h2>Alerts ({len(alerts)})</h2>
        {"".join(f'<div class="alert {a["severity"]}">{a["message"]}</div>' for a in alerts) if alerts else '<p style="color: #4caf50;">✓ No alerts</p>'}
        
        <h2>Windows Data</h2>
        <table style="width: 100%; border-collapse: collapse;">
            <tr style="background: #f0f0f0;">
                <th style="border: 1px solid #ddd; padding: 8px;">Window</th>
                <th style="border: 1px solid #ddd; padding: 8px;">Tickets</th>
                <th style="border: 1px solid #ddd; padding: 8px;">Acceptance</th>
                <th style="border: 1px solid #ddd; padding: 8px;">Rejection</th>
                <th style="border: 1px solid #ddd; padding: 8px;">Quality</th>
                <th style="border: 1px solid #ddd; padding: 8px;">Confidence</th>
            </tr>
            {"".join(f'<tr>' +
                     f'<td style="border: 1px solid #ddd; padding: 8px;">{w["window_id"]}</td>' +
                     f'<td style="border: 1px solid #ddd; padding: 8px;">{w["size"]}</td>' +
                     f'<td style="border: 1px solid #ddd; padding: 8px;">{w["acceptance_rate"]:.1%}</td>' +
                     f'<td style="border: 1px solid #ddd; padding: 8px;">{w["rejection_rate"]:.1%}</td>' +
                     f'<td style="border: 1px solid #ddd; padding: 8px;">{w["avg_quality"]:.3f}</td>' +
                     f'<td style="border: 1px solid #ddd; padding: 8px;">{w["avg_confidence"]:.3f}</td>' +
                     f'</tr>' for w in windows)}
        </table>
    </div>
    
    <script>
        var trace = {{
            x: {window_ids},
            y: {acceptance_rates},
            mode: 'lines+markers',
            name: 'Acceptance Rate',
            line: {{color: '#2196F3', width: 3}},
            marker: {{size: 8}}
        }};
        
        var layout = {{
            title: 'Acceptance Rate Over Time',
            xaxis: {{title: 'Window ID'}},
            yaxis: {{title: 'Acceptance Rate (%)', range: [0, 100]}},
            hovermode: 'closest',
            plot_bgcolor: '#f9f9f9',
            paper_bgcolor: 'white'
        }};
        
        Plotly.newPlot('trend-chart', [trace], layout);
    </script>
</body>
</html>
"""
        # Save files
        with open("data/drift_dashboard.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        
        with open("data/drift_dashboard.html", "w", encoding="utf-8") as f:
            f.write(html)
        
        return html


if __name__ == "__main__":
    dashboard = AcceptanceRateDashboard()
    data = dashboard.generate_dashboard_data()
    
    # Print text report
    print("=" * 80)
    print("ACCEPTANCE RATE DRIFT DASHBOARD")
    print("=" * 80)
    print()
    print("CURRENT METRICS:")
    print(f"  Acceptance Rate: {data['current_metrics']['acceptance_rate']:.1%}")
    print(f"  Rejection Rate: {data['current_metrics']['rejection_rate']:.1%}")
    print(f"  Edit Rate: {data['current_metrics']['edit_rate']:.1%}")
    print()
    print("DRIFT ANALYSIS:")
    print(f"  Mean Acceptance: {data['drift_analysis']['statistics']['mean_acceptance']:.1%}")
    print(f"  Std Dev: ±{data['drift_analysis']['statistics']['std_dev_acceptance']:.1%}")
    print(f"  Trend: {data['drift_analysis']['statistics']['trend']}")
    print(f"  Drift Detected: {data['drift_analysis']['drift_detected']}")
    print()
    
    if data['drift_analysis']['alerts']:
        print("ALERTS:")
        for alert in data['drift_analysis']['alerts']:
            print(f"  [{alert['severity'].upper()}] {alert['message']}")
    else:
        print("ALERTS: None")
    
    print("=" * 80)
    
    # Save data
    with open("data/drift_dashboard.json", "w") as f:
        json.dump(data, f, indent=2)
    
    # Save HTML
    html = dashboard.generate_html_report(data)
    with open("data/drift_dashboard.html", "w") as f:
        f.write(html)
    
    print("\n✓ Dashboard data saved to data/drift_dashboard.json")
    print("✓ HTML report saved to data/drift_dashboard.html")
