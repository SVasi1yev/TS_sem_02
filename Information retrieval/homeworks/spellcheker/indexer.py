from LanguageModel import LanguageModel
from ErrorModel import ErrorModel

lang_model = LanguageModel()
lang_model.fit()
lang_model.store()

err_model = ErrorModel()
err_model.fit()
err_model.store()
