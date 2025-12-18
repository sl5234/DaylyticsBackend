from pydantic import BaseModel
from typing import List, Optional


class Step(BaseModel):
    """
    A single step in a workflow.

    Represents one step in the analysis workflow with the tool to use,
    description of what the step does, and reference to the next step.
    """

    name: str
    description: str
    tool: str
    next: Optional[str] = None  # the name of the subsequent Step


class Workflow(BaseModel):
    """
    A workflow consisting of an ordered sequence of steps.

    The workflow defines the sequence of tools and operations needed
    to process a user's request.
    """

    start: str  # the name of the first Step
    graph: List[Step]
