import os
import yaml
import requests
from kubernetes import client, config
from dotenv import load_dotenv
import time
import logging

class ScalePilot:
    def __init__(self):
        load_dotenv()
        self.config = {
            "event_name": os.getenv("EVENT_NAME"),
            "webhook_url": os.getenv("SLACK_WEBHOOK_URL"),
            "namespace": os.getenv("NAMESPACE", "nanovest"),
            "sleep_time": int(os.getenv("SLEEP_TIME", 900)),
            "event_config_file": "config.yaml",
            "original_values": {},
        }
    
    def load_event_config(self, file_path):
        """Load event configuration from a YAML file."""
        try:
            with open(file_path, "r") as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            logging.error(f"Event configuration file not found: {file_path}")
            exit(1)
        except yaml.YAMLError as e:
            logging.error(f"Error loading event configuration: {e}")
            exit(1)
        
    def check_event_config(self):  
        event_name = self.config["event_name"]
        slack_webhook_url = self.config["webhook_url"]
        event_config = self.load_event_config(self.config["event_config_file"])
        services = event_config.get(event_name)
        
        if not slack_webhook_url or not event_name or not event_config or not services:
            if not slack_webhook_url:
              logging.error("Env variable SLACK_WEBHOOK_URL is not set.")
            if not event_name:
              logging.error("Env variable EVENT_NAME is not set.")
            if not event_config:
              logging.error("No event configuration found.")
            if not services:
                logging.error(f"No configuration found for Eventname: {event_name}")
            exit(1)
        
        return services
        
    def send_slack_notification(self, message):
        """Send a message to Slack via webhook."""
        headers = {"Content-Type": "application/json"}
        payload = {"text": message}
        try:
            response = requests.post(self.config["webhook_url"], json=payload, headers=headers)
            response.raise_for_status()
            logging.info("Slack notification sent successfully.")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error sending Slack notification: {e}")

    def format_success_message(self, service_name, old_min, new_min):
        """Format a Slack message for successful updates."""
        return (
            f"> *Service:* `{service_name}`\n"
            f"> *Updated Replica Count:* {old_min} :arrow_right: {new_min}\n"
            f"> *Scaling Completed!* :white_check_mark:"
        )

    def format_error_message(self, service_name, error):
        """Format a Slack message for failed updates."""
        return (
            f"> *Service:* `{service_name}`\n"
            f"> *Failed to Scale service* :x:\n"
            f"> *Error:* {error}"
        )

    def update_hpa(self, service_name, min_count):
        """Update the HPA for a given service and notify via Slack."""
        config.load_kube_config()  # Use config.load_incluster_config() if running inside a cluster
        api = client.AutoscalingV2Api()
        namespace = self.config["namespace"]
        try:
            if min_count is None or min_count < 1:
                message = f"Invalid minCount value for service {service_name}"
                # self.send_slack_notification(self.format_error_message(service_name, message))
                logging.error(message)
                exit(1)
            hpa = api.read_namespaced_horizontal_pod_autoscaler(service_name, namespace)
            old_min = hpa.spec.min_replicas
            self.config["original_values"][service_name] = old_min
            hpa.spec.min_replicas = min_count
            api.patch_namespaced_horizontal_pod_autoscaler(service_name, namespace, hpa)
            message = self.format_success_message(service_name, old_min, min_count)
            logging.info(message)
            # self.send_slack_notification(message)
        except client.exceptions.ApiException as e:
            error_message = (
                f"HPA for service {service_name} not found in namespace {namespace}."
                if e.status == 404
                else str(f"Error updating HPA for service {service_name}")
            )
            message = self.format_error_message(service_name, error_message)
            logging.error(e)
            # self.send_slack_notification(message)
            exit(1)

    def sleep_temporarily(self):
        sleep_time = self.config["sleep_time"]
        logging.info(f"Waiting for {sleep_time} seconds before reverting HPA changes.")
        time.sleep(sleep_time)
        
    def revert_hpa(self):
        """Revert the HPA to the original minCount values."""
        api = client.AutoscalingV2Api()
        namespace = self.config["namespace"]
        for service_name, original_min in self.config["original_values"].items():
            try:
                hpa = api.read_namespaced_horizontal_pod_autoscaler(service_name, namespace)
                hpa.spec.min_replicas = original_min
                api.patch_namespaced_horizontal_pod_autoscaler(service_name, namespace, hpa)
                message = (
                    f"> *Service:* `{service_name}`\n"
                    f"> *Scaled Down successfully* :white_check_mark: \n"
                    f"> *Reverted Min Count:* {original_min}"
                )
                logging.info(message)
                # self.send_slack_notification(message)
            except client.exceptions.ApiException as e:
                error_message = f"Failed to revert HPA for {service_name}: {str(e)}"
                logging.error(error_message)
                # self.send_slack_notification(self.format_error_message(service_name, error_message))

    def run(self):
        
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

        services = self.check_event_config()
        # self.send_slack_notification(f":loading: *Scaling Workloads for NanoPlay :arrow_right: {self.config['event_name']}* :loading:")
        for service in services:
            self.update_hpa(service["name"], service["minCount"])

        self.sleep_temporarily()
        self.revert_hpa()

if __name__ == "__main__":
    scaler = ScalePilot()
    scaler.run()
