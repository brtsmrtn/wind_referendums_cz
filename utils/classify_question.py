import data.types

def classify_question(question: str) -> data.types.QuestionClassificationResult:
    """Classifies a question based on its stance toward turbine construction.

    Determines whether the question supports, opposes, or is neutral/unknown
    regarding turbine construction by checking for specific keywords.

    Args:
        question (str): The input question to classify.

    Returns:
        Literal["pro_turbines", "anti_turbines", "unknown"]:
            - "pro_turbines": If the question supports turbine construction.
            - "anti_turbines": If the question opposes turbine construction.
            - "unknown": If the stance cannot be determined.

    Examples:
        >>> classify_question("Souhlasíte s umístěním [...] větrných elektráren v katastrálním území [...]?")
        "pro_turbines"
        >>> classify_question("Souhlasíte s tím, aby zastupitelstvo [...] již nepodnikalo žádné kroky směřující k výstavbě větrných elektráren [...]?")
        "anti_turbines"
    """
    question = question.lower()
    support_keywords = [
        "souhlasíte s výstavbou",
        " umožnily umístění",
        "podpoře výstavby",
        " byly postaveny",
        ", byla realizována výstavba",
        " umožnili umístění ",
        ", podnikalo kroky směřující k výstavbě",
        "souhlasíte s umístěním",
        "souhlasím s výstavbou",
        " byly postaveny a provozovány",
        " podporovalo rozšíření ",
        " provést veškeré úkony pro pořízení územního plánu obce tak, aby obsahoval vymezení pozemků pro výstavbu větrných elektráren?",
        "umožnily umístění jedné ",
        "s tím, aby byly ",
        " provést veškeré úkony pro pořízení územního plánu obce tak, aby obsahoval vymezení pozemků pro výstavbu větrných elektráren",
        " došlo k výstavbě",
        " podnikat další kroky, směřující k výstavbě",
        " s výstavbou větrných elektráren ",
        "souhlasíte se stavbou větrné",
        " byly za níže uvedených podmínek postaveny "]
    oppose_keywords = [
        "zamezilo výstavbě",
        "nepovolovalo",
        "zakázalo",
        "nepodnikalo kroky směřující k výstavbě",
        "směřující k zamezení",
        "nemohla vzniknout plocha, která by umožňovala výstavbu",
        "nepodnikalo žádné kroky",
        "zastavilo všechny kroky"]

    if any(keyword in question for keyword in support_keywords):
        return "pro_turbines"
    elif any(keyword in question for keyword in oppose_keywords):
        return "anti_turbines"
    else:
        return "unknown"
    