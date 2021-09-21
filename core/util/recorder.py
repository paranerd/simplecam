class Recorder:
  def start_recording(self, path):
    """
    Abstract method to be implemented by all recorders.

    @param string path
    """
    raise NotImplementedError("start_recording() is not implemented")

  def stop_recording(self):
    """Abstract method to be implemented by all recorders."""
    raise NotImplementedError("stop_recording() is not implemented")
