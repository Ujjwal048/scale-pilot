# Scale Pilot

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.9-blue.svg)](https://www.python.org/downloads/)

Scale Pilot is a Kubernetes-based automation tool designed to dynamically manage Horizontal Pod Autoscaler (HPA) configurations based on predefined events. It provides a flexible and configurable way to scale your Kubernetes workloads up or down according to specific events or schedules.

## Features

- 🔄 Dynamic HPA min-replica count management
- ⏰ Configurable event-based scaling
- 🔔 Slack notifications for scaling events
- 🔄 Automatic reversion of scaling changes
- 📝 YAML-based configuration
- 🔒 Kubernetes-native implementation

## Use Cases

- Event-driven scaling for high-traffic periods
- Scheduled scaling for maintenance windows
- Automated scaling for special events or promotions
- Temporary capacity adjustments

## Prerequisites

- Kubernetes cluster
- Python 3.9+
- Kubernetes Python client
- External Secrets Operator installed in the cluster
- GCP Secret Manager (or other supported secret provider)
- Slack webhook URL (for notifications)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/scale-pilot.git
cd scale-pilot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure External Secrets:
   - Navigate to the `k8s` directory
   - Update the namespace in `gcp-external-secrets.yaml` to your target namespace
   - Create the following secrets in your GCP Secret Manager:
     - `scale-pilot-config-file`: Contains your scaling configuration
     - `scale-pilot-env`: Contains environment variables
     - `scale-pilot-eventname`: Contains the eventname and the corresponding value from config file is selected for scaling.
   - Apply the external secrets:
     ```bash
     kubectl apply -f k8s/gcp-external-secrets.yaml
     ```

4. Deploy the CronJob:
   ```bash
   kubectl apply -f k8s/cronjob.yaml
   ```

## Configuration

Store your configuration in GCP Secret Manager with the following structure:

```yaml
eventName-1:
  - name: hpa-1
    minCount: 4
  - name: hpa-2
    minCount: 5
eventName-2:
  - name: hpa-1
    minCount: 4
  - name: hpa-2
    minCount: 5
```

Required environment variables in `scale-pilot-env`:
```
SLACK_WEBHOOK_URL=your_slack_webhook_url
SLEEP_TIME=900
NAMESPACE=your_namespace
```

Required environment variables in `scale-pilot-eventname`:
```
EVENT_NAME=<Must match any of the elements in config.yaml>
```

## Architecture

Scale Pilot operates as a Kubernetes CronJob that:
1. Reads event configurations from mounted secrets
2. Updates HPA min-replica counts
3. Sends notifications via Slack
4. Reverts changes after a configurable period

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues or have questions, please [open an issue](https://github.com/yourusername/scale-pilot/issues) on GitHub.

## Acknowledgments

- Kubernetes Python Client
- Python-dotenv
- PyYAML
- External Secrets Operator
