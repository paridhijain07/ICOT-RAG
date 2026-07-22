from rag_icot.components.reasoning_engine import ReasoningEngine
from rag_icot.components.answer_generator import AnswerGenerator


class RAGICOTPipeline:

    def __init__(self):

        self.engine = ReasoningEngine()

        self.generator = AnswerGenerator()

    def run(
        self,
        question
    ):

        documents = self.engine.reason(
            question
        )

        answer = self.generator.generate(
            question,
            documents
        )

        return answer