"""Composed behavior mixin for Workitem."""

from .attachments import WorkitemAttachmentMixin
from .lifecycle import WorkitemLifecycleMixin
from .links import WorkitemLinkMixin
from .teststeps import WorkitemTestStepMixin
from .users import WorkitemUserMixin
from .workflow import WorkitemWorkflowMixin


class WorkitemActionsMixin(
    WorkitemUserMixin,
    WorkitemWorkflowMixin,
    WorkitemLinkMixin,
    WorkitemAttachmentMixin,
    WorkitemTestStepMixin,
    WorkitemLifecycleMixin,
):
    """Composite mixin keeping original Workitem behavior surface."""
