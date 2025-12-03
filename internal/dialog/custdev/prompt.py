from internal import interface, model


class CustDevPromptGenerator(interface.ICustDevPromptGenerator):
    async def get_custdev_system_prompt(self, questions: model.CustDevQuestions) -> str:
        return f"""
"""