# src/kibana_mcp/tools/__init__.py

# Import implementation functions from their respective modules
from .alerts.tag_alert import _call_tag_alert
from .alerts.adjust_alert_status import _call_adjust_alert_status
from .alerts.get_alerts import _call_get_alerts

from .rules.get_rule import _call_get_rule
from .rules.delete_rule import _call_delete_rule
from .rules.update_rule_status import _call_update_rule_status
from .rules.find_rules import _call_find_rules
from .rules.get_prepackaged_rules_status import _call_get_prepackaged_rules_status
from .rules.install_prepackaged_rules import _call_install_prepackaged_rules

from .exceptions.get_rule_exceptions import _call_get_rule_exceptions
from .exceptions.add_rule_exception_items import _call_add_rule_exception_items
from .exceptions.create_exception_list import _call_create_exception_list
from .exceptions.associate_shared_exception_list import _call_associate_shared_exception_list

# Import saved objects tools
from .saved_objects.find_objects import _call_find_objects
from .saved_objects.get_object import _call_get_object
from .saved_objects.bulk_get_objects import _call_bulk_get_objects
from .saved_objects.create_object import _call_create_object
from .saved_objects.update_object import _call_update_object
from .saved_objects.delete_object import _call_delete_object
from .saved_objects.export_objects import _call_export_objects
from .saved_objects.import_objects import _call_import_objects

# Import endpoint tools
from .endpoint.isolate_endpoint import _call_isolate_endpoint
from .endpoint.unisolate_endpoint import _call_unisolate_endpoint
from .endpoint.run_command_on_endpoint import _call_run_command_on_endpoint
from .endpoint.get_response_actions import _call_get_response_actions
from .endpoint.get_response_action_details import _call_get_response_action_details
from .endpoint.get_response_action_status import _call_get_response_action_status
from .endpoint.kill_process import _call_kill_process
from .endpoint.suspend_process import _call_suspend_process
from .endpoint.scan_endpoint import _call_scan_endpoint
from .endpoint.get_file_info import _call_get_file_info
from .endpoint.download_file import _call_download_file

# Import utility function
from .utils._utils import execute_tool_safely

# Define what gets imported when someone imports the package
__all__ = [
    # Alert tools
    '_call_tag_alert',
    '_call_adjust_alert_status',
    '_call_get_alerts',

    # Rule tools
    '_call_get_rule',
    '_call_delete_rule',
    '_call_update_rule_status',
    '_call_get_prepackaged_rules_status',
    '_call_install_prepackaged_rules',

    # Exception tools
    '_call_get_rule_exceptions',
    '_call_add_rule_exception_items',
    '_call_create_exception_list',
    '_call_associate_shared_exception_list',

    # Saved Objects tools
    '_call_find_objects',
    '_call_get_object',
    '_call_bulk_get_objects',
    '_call_create_object',
    '_call_update_object',
    '_call_delete_object',
    '_call_export_objects',
    '_call_import_objects',

    # Endpoint tools
    '_call_isolate_endpoint',
    '_call_unisolate_endpoint',
    '_call_run_command_on_endpoint',
    '_call_get_response_actions',
    '_call_get_response_action_details',
    '_call_get_response_action_status',
    '_call_kill_process',
    '_call_suspend_process',
    '_call_scan_endpoint',
    '_call_get_file_info',
    '_call_download_file',

    # Utils
    'execute_tool_safely'
]
