from copy import deepcopy
from typing import List, Optional

import structlog
from database import Category, Strain
from pydantic_forms.core import FormPage, post_form, register_form
from pydantic_forms.exceptions import FormValidationError
from pydantic_forms.types import FormGenerator, State
from pydantic_forms.validators import Choice

logger = structlog.get_logger(__name__)


def create_ticket_form(current_state: dict) -> FormGenerator:
    strains = Strain.query.all()

    StrainChoice = Choice(
        "StrainChoice",
        zip(
            [str(strain.id) for strain in strains],
            [(strain.name, strain.name) for strain in strains],
        ),  # type: ignore
    )

    categories = Category.query.all()

    CategoryChoice = Choice(
        "CategoryChoice",
        zip(
            [str(category.id) for category in categories],
            [(category.name, category.name) for category in categories],
        ),  # type: ignore
    )

    class ProductForm(FormPage):
        class Config:
            title = "New product"

        product_name: str
        strain_name: str
        strain_choice: StrainChoice
        category_choice: CategoryChoice

    user_input = yield ProductForm

    class Product2Form(FormPage):
        class Config:
            title = "Extra info"

        info: str
        long_info: bool

    user_input2 = yield Product2Form
    return user_input.dict()



#
# def start_form(
#     form_key: str,
#     user_inputs: Optional[List[State]] = None,
#     user: str = "Just a user",  # Todo: check if we need users inside form logic?
# ) -> State:
#     """Setup a empty form.
#
#     Args:
#         form_key: name of workflow
#         user_inputs: List of form inputs from frontend
#         user: User who starts this process
#
#     Returns:
#         The data that the user entered into the form
#
#     """
#     if user_inputs is None:
#         # Ensure the first FormNotComplete is raised from Swagger and when a POST is done without user_inputs:
#         user_inputs = []
#
#     # form = get_form(form_key)
#
#     # if not form:
#     #     raise_status(HTTPStatus.NOT_FOUND, "Form does not exist")
#
#     # Todo: decide what we want for initial input
#     initial_state = {
#         "form_key": "create_ticket_form",
#     }
#
#     try:
#         state = post_form(create_ticket_form, initial_state, user_inputs)
#     except FormValidationError:
#         logger.exception("Validation errors", user_inputs=user_inputs)
#         raise
#
#     return state
