from typing import Literal, Union

# Define a reusable type for the classification result
QuestionClassificationResult = Literal["pro_turbines", "anti_turbines", "unknown"]

# Define a type for the result of the extraction
# Input: '102 (39.53%)' -> '102' / '39.53'
VoteExtractionResult = Union[int, float]

# Define a type for the extraction mode
ExtractionType = Literal["count", "percent"]

# Define a type for the referendum binding status
ReferendumBindingStatus = bool

# Define a type for the referendum validity status
ReferendumValidityStatus = bool

# Define a type for the voting validity status
VotingValidityStatus = bool

# Define a type for the binding minimum count result
BindingMinimumCount = int