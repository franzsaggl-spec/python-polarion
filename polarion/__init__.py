from .document import DocumentCreator
from .factory import addCreator
from .plan import PlanCreator
from .testrun import TestrunCreator
from .user import UserCreator
from .workitem import WorkitemCreator

addCreator("workitem", WorkitemCreator)
addCreator("testrun", TestrunCreator)
addCreator("user", UserCreator)
addCreator("module", DocumentCreator)
addCreator("plan", PlanCreator)
