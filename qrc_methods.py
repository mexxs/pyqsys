from jsonrpcclient import request


class BaseMethods(object):
    def __init__(self, core):
        self.core = core

    @staticmethod
    def _build_cmd(method: str, params=None) -> dict:
        return request(method, params=params)

    def _send(self, method: str, params=None) -> dict:
        cmd = self._build_cmd(method, params)
        if self.core.sock_thread.is_alive():
            self.core.msg_queue.put(cmd)
            self.core.response_is_ready.wait()
            return self.core.parse_response(cmd["id"], self.core.response_queue.get())
        else:
            print("Request could not be sent. There is no active connection to the core.")


class ControlMethods(BaseMethods):
    """
      Implementation of QRC Control Methods

      Control.Get
      Control.Set
    """

    def __init__(self, core):
        super(ControlMethods, self).__init__(core)
        self.method_start: str = "Control."

    def get(self, names: list = None) -> dict:
        method_name: str = self.method_start + "Get"
        if not names:
            raise AttributeError("Control.Get needs a control name or a list of names.")
        if isinstance(names, list):
            params: list = names
        elif isinstance(names, str):
            params: list = [names]
        else:
            raise ValueError("Must either give one string or a list of strings as arguments.")
        return self._send(method_name, params)

    def set(self, name: str = None, value=None, ramp=None) -> dict:
        method_name: str = self.method_start + "Set"
        if not name or not value:
            raise AttributeError("Control.Set needs a name and a value. Ramp is optional.")
        if ramp:
            params: dict = {"Name": name, "Value": value, "Ramp": ramp}
        else:
            params: dict = {"Name": name, "Value": value}
        return self._send(method_name, params)


class ComponentMethods(BaseMethods):
    """
      Implementation of QRC Component Control Methods

      Component.Get
      Component.GetControls
      Component.GetComponents
      Component.Set
    """

    def __init__(self, core):
        super(ComponentMethods, self).__init__(core)
        self.method_start: str = "Component."

    def get(self, name: str = None, controls: list = None) -> dict:
        # Returns the values of one or more specified controls within a specified Named Component.
        # name: str
        # controls: list of dicts

        method_name: str = self.method_start + "Get"
        if not name or not controls:
            raise AttributeError("Component.Get needs a Component name and array of control values (dictionary)")
        if isinstance(name, str) and isinstance(controls, list):
            params: dict = {"Name": name, "Controls": controls}
        else:
            raise ValueError("Component.Get needs a name (str) and an array of dictionaries with controls.")
        return self._send(method_name, params)

    def get_controls(self, name: str = None) -> dict:
        # Returns a table of all controls and their values in a specified Named Component.
        # name: str

        if not name:
            raise AttributeError("Component.GetControls needs a name (str) of a Component")
        else:
            params: dict = {"Name": name}
        method_name: str = self.method_start + "GetControls"
        return self._send(method_name, params)

    def get_components(self) -> dict:
        # Get a list of all named components in a design, along with their type and properties.
        method_name: str = self.method_start + "GetComponents"
        return self._send(method_name)

    def set(self, name: str = None, controls: list = None) -> dict:
        # Set one or more controls for a single named component. Returns a list of unknown controls after processing.
        # name: str
        # controls: list of dicts

        if not name or not controls:
            raise AttributeError("Component.Set needs a Component name and an array of dictionaries with controls.")
        if isinstance(name, str) and isinstance(controls, list):
            params: dict = {"Name": name, "Control": controls}
        else:
            raise ValueError("Component.Set needs a name (str) and an array of dictionaries with controls.")
        method_name: str = self.method_start + "Set"
        return self._send(method_name, params)


class ChangeGroupMethods(BaseMethods):
    """
      Implementation of QRC Change Group Methods

      ChangeGroup.AddControl
      ChangeGroup.AddComponentControl
      ChangeGroup.Remove
      ChangeGroup.Poll
      ChangeGroup.Destroy
      ChangeGroup.Invalidate
      ChangeGroup.Clear
      ChangeGroup.AutoPoll
    """

    def __init__(self, core):
        super(ChangeGroupMethods, self).__init__(core)
        self.method_start: str = "ChangeGroup."

    def add_control(self, cgroup_id: str, controls_array: list) -> dict:
        method_name: str = self.method_start + "AddControl"
        params: dict = {"Id": cgroup_id, "Controls": controls_array}
        return self._send(method_name, params)

    def add_component_control(self, cgroup_id: str, component_name: str, controls: list) -> dict:
        method_name: str = self.method_start + "AddComponentControl"
        params: dict = {"Id": cgroup_id, "Component": {"Name": component_name, "Controls": controls}}
        return self._send(method_name, params)

    def remove(self, cgroup_id: str, controls_array: list) -> dict:
        method_name: str = self.method_start + "Remove"
        params: dict = {"Id": cgroup_id, "Controls": controls_array}
        return self._send(method_name, params)

    def poll(self, cgroup_id: str) -> dict:
        method_name: str = self.method_start + "Poll"
        params: dict = {"Id": cgroup_id}
        return self._send(method_name, params)

    def destroy(self, cgroup_id: str) -> dict:
        method_name: str = self.method_start + "Destroy"
        params: dict = {"Id": cgroup_id}
        return self._send(method_name, params)

    def invalidate(self, cgroup_id: str) -> dict:
        method_name: str = self.method_start + "Invalidate"
        params: dict = {"Id": cgroup_id}
        return self._send(method_name, params)

    def clear(self, cgroup_id: str) -> dict:
        method_name: str = self.method_start + "Clear"
        params: dict = {"Id": cgroup_id}
        return self._send(method_name, params)

    def auto_poll(self, cgroup_id: str, rate: int) -> dict:
        method_name: str = self.method_start + "AutoPoll"
        params: dict = {"Id": cgroup_id, "Rate": rate}
        return self._send(method_name, params)


class MixerMethods(BaseMethods):
    """
      Implementation of QRC Mixer Methods

      For channel string syntax see: https://q-syshelp.qsc.com/Content/External_Control_APIs/QRC/QRC_Commands.htm#Input

      Mixer.SetCrossPointGain
      Mixer.SetCrossPointDelay
      Mixer.SetCrossPointMute
      Mixer.SetCrossPointSolo
      Mixer.SetInputGain
      Mixer.SetInputMute
      Mixer.SetInputSolo
      Mixer.SetOutputGain
      Mixer.SetOutputMute
      Mixer.SetCueMute
      Mixer.SetCueGain
      Mixer.SetInputCueEnable
      Mixer.SetInputCueAfl
    """

    def __init__(self, core):
        super(MixerMethods, self).__init__(core)
        self.method_start: str = "Mixer."

    def set_xpoint_gain(self, mixer_name: str, inputs: str, outputs: str, gain_value: float, ramp: float) -> dict:
        method_name: str = self.method_start + "SetCrossPointGain"
        params: dict = {"Name": mixer_name, "Inputs": inputs, "Outputs": outputs, "Value": gain_value, "Ramp": ramp}
        return self._send(method_name, params)

    def set_xpoint_delay(self, mixer_name: str, inputs: str, outputs: str, delay_value: float, ramp: float) -> dict:
        method_name: str = self.method_start + "SetCrossPointDelay"
        params: dict = {"Name": mixer_name, "Inputs": inputs, "Outputs": outputs, "Value": delay_value, "Ramp": ramp}
        return self._send(method_name, params)

    def set_xpoint_mute(self, mixer_name: str, inputs: str, outputs: str, mute_value: bool) -> dict:
        method_name: str = self.method_start + "SetCrossPointMute"
        params: dict = {"Name": mixer_name, "Inputs": inputs, "Outputs": outputs, "Value": mute_value}
        return self._send(method_name, params)

    def set_xpoint_solo(self, mixer_name: str, inputs: str, outputs: str, solo_value: bool) -> dict:
        method_name: str = self.method_start + "SetCrossPointSolo"
        params: dict = {"Name": mixer_name, "Inputs": inputs, "Outputs": outputs, "Value": solo_value}
        return self._send(method_name, params)

    def set_input_gain(self, mixer_name: str, inputs: str, gain_value: float, ramp: float) -> dict:
        method_name: str = self.method_start + "SetInputGain"
        params: dict = {"Name": mixer_name, "Inputs": inputs, "Value": gain_value, "Ramp": ramp}
        return self._send(method_name, params)

    def set_input_mute(self, mixer_name: str, inputs: str, mute_value: bool) -> dict:
        method_name: str = self.method_start + "SetInputMute"
        params: dict = {"Name": mixer_name, "Inputs": inputs, "Value": mute_value}
        return self._send(method_name, params)

    def set_input_solo(self, mixer_name: str, inputs: str, solo_value: bool) -> dict:
        method_name: str = self.method_start + "SetInputSolo"
        params: dict = {"Name": mixer_name, "Inputs": inputs, "Value": solo_value}
        return self._send(method_name, params)

    def set_output_gain(self, mixer_name: str, outputs: str, gain_value: float, ramp: float) -> dict:
        method_name: str = self.method_start + "SetOutputGain"
        params: dict = {"Name": mixer_name, "Outputs": outputs, "Value": gain_value, "Ramp": ramp}
        return self._send(method_name, params)

    def set_output_mute(self, mixer_name: str, outputs: str, mute_value: bool) -> dict:
        method_name: str = self.method_start + "SetOutputMute"
        params: dict = {"Name": mixer_name, "Outputs": outputs, "Value": mute_value}
        return self._send(method_name, params)

    def set_cue_mute(self, mixer_name: str, cues: str, mute_value: bool) -> dict:
        method_name: str = self.method_start + "SetCueMute"
        params: dict = {"Name": mixer_name, "Cues": cues, "Value": mute_value}
        return self._send(method_name, params)

    def set_cue_gain(self, mixer_name: str, cues: str, gain_value: float, ramp: float) -> dict:
        method_name: str = self.method_start + "SetCueGain"
        params: dict = {"Name": mixer_name, "Cues": cues, "Value": gain_value, "Ramp": ramp}
        return self._send(method_name, params)

    def set_input_cue_enable(self, mixer_name: str, cues: str, inputs: str, enable_value: bool) -> dict:
        method_name: str = self.method_start + "SetInputCueEnable"
        params: dict = {"Name": mixer_name, "Cues": cues, "Inputs": inputs, "Value": enable_value}
        return self._send(method_name, params)

    def set_input_cue_afl(self, mixer_name: str, cues: str, inputs: str, afl_value: bool) -> dict:
        method_name: str = self.method_start + "SetInputCueAfl"
        params: dict = {"Name": mixer_name, "Cues": cues, "Inputs": inputs, "Value": afl_value}
        return self._send(method_name, params)


class LoopPlayerMethods(BaseMethods):
    """
      Implementation of QRC Loop Player Methods

      LoopPlayer.Start
      LoopPlayer.Stop
      LoopPlayer.Cancel
    """

    def __init__(self, core):
        super(LoopPlayerMethods, self).__init__(core)
        self.method_start: str = "LoopPlayer."

    def start(self, loopplayer_name: str, start_time: int, files_array: list, loop: bool, log: bool, seek: int) -> dict:
        method_name: str = self.method_start + "Start"
        params: dict = {
            "Files": files_array,
            "Name": loopplayer_name,
            "StartTime": start_time,
            "Loop": loop,
            "Log": log,
            "Seek": seek
        }
        return self._send(method_name, params)

    def stop(self, loopplayer_name: str, outputs, log: bool) -> dict:
        method_name: str = self.method_start + "Stop"
        params: dict = {"Name": loopplayer_name, "Outputs": outputs, "Log": log}
        return self._send(method_name, params)

    def cancel(self, loopplayer_name: str, outputs, log: bool) -> dict:
        method_name: str = self.method_start + "Cancel"
        params: dict = {"Name": loopplayer_name, "Outputs": outputs, "Log": log}
        return self._send(method_name, params)


class SnapshotMethods(BaseMethods):
    """
      Implementation of QRC Snapshot Methods

      Snapshot.Load
      Snapshot.Save
    """

    def __init__(self, core):
        super(SnapshotMethods, self).__init__(core)
        self.method_start: str = "Snapshot."

    def load(self, bank_name: str, bank: int, ramp: float) -> dict:
        method_name: str = self.method_start + "Load"
        params: dict = {"Name": bank_name, "Bank": bank, "Ramp": ramp}
        return self._send(method_name, params)

    def save(self, bank_name: str, bank: int) -> dict:
        method_name: str = self.method_start + "Save"
        params: dict = {"Name": bank_name, "Bank": bank}
        return self._send(method_name, params)
