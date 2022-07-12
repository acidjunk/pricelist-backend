from typing import List, Optional

import structlog
from pydantic_forms.core import post_form, FormPage
from pydantic_forms.exceptions import FormValidationError
from pydantic_forms.types import State, FormGenerator

logger = structlog.get_logger(__name__)


def create_ticket_form(current_state: dict) -> FormGenerator:
    class ProductForm(FormPage):
        class Config:
            title = "New product"

        product_name: str

    user_input = yield ProductForm
    return user_input.dict()


def start_form(
    form_key: str,
    user_inputs: Optional[List[State]] = None,
    user: str = "Just a user",  # Todo: check if we need users inside form logic?
) -> State:
    """Setup a empty form.

    Args:
        form_key: name of workflow
        user_inputs: List of form inputs from frontend
        user: User who starts this process

    Returns:
        The data that the user entered into the form

    """
    if not user_inputs or user_inputs == [{}]:
        # Ensure the first FormNotComplete is raised from Swagger and when a POST is done without user_inputs:
        user_inputs = []

    # form = get_form(form_key)

    # if not form:
    #     raise_status(HTTPStatus.NOT_FOUND, "Form does not exist")

    # Todo: decide what we want for initial input
    initial_state = {
        "form_key": create_ticket_form,
    }

    try:
        state = post_form(create_ticket_form, initial_state, user_inputs)
    except FormValidationError:
        logger.exception("Validation errors", user_inputs=user_inputs)
        raise

    return state
