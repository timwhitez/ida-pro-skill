#
# Default-safe setting:
# - False: only localhost and this machine's local Windows or WSL addresses may connect
# - True: allow clients from other machines on reachable network interfaces
#
REMOTE_ACCESS = False

from ida_pro_skill_plugin_runtime.bridge import IdaProSkillBridgePlugin


def PLUGIN_ENTRY():
    return IdaProSkillBridgePlugin(remote_access=REMOTE_ACCESS)
