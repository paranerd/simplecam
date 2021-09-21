class Detector:
  def detected(self):
    """
    Abstract method to be implemented by all detectors.

    @return bool
    """
    raise NotImplementedError("detected() is not implemented")
