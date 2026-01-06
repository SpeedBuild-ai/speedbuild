from pydantic import BaseModel, Field

from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage

from ..rate_limiter.rateLimiter import LLMRateLimiter

from ..prompts.classifier_prompt import system_prompt

from speedbuild.utils.config.agent_config import getLLMConfig

class ClassifierOutput(BaseModel):
	classification : str = Field(description="Feature classification type, could be : REUSABLE, SEMI_REUSABLE, or NOT_REUSABLE")
	# reason : str = Field(description="Explain why this snippet is or isn't useful for pattern governance and reuse.")
	# ai_reuse_recommendation : str = Field(description="How the AI should use this feature when requested via MCP")


class FeatureClassifier():
	def __init__(self,framework):
		provider,model_name,api_key = getLLMConfig("classification")
		model = init_chat_model(model_provider=provider, model=model_name, api_key=api_key)
		self.model = model.with_structured_output(ClassifierOutput)
		self.framework = framework
		self.rate_limmiter_manager = LLMRateLimiter()

	# TODO : use rate limit class 

	async def classifyFeature(self,feature_code):

		response = await self.rate_limmiter_manager.call(
            self.model,
            input = [
				SystemMessage(content=system_prompt),
				HumanMessage(content=feature_code.strip())
			]
        )

		return response
	