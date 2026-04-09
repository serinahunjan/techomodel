def calculate_dimensions(answers: list[int]) -> dict:
    """
    calculates the three technostress dimension scores from 30 survey responses.
    Surevy is structured to three grps of qs.
    Q1-Q10= techno-overload
    Q11-Q20= Techno-invasion
    Q21-Q30= Techno-complexity

    each of the anwsers is summed up to produce a score for that dimension.
    """
    # list below presents the question numbers belonging to each dimension.
    # the lists are question numbers, not index based
    OVERLOAD_QS = [1, 2, 3, 4, 5]
    INVASION_QS = [6, 7, 8, 9, 10]
    COMPLEXITY_QS = [11, 12, 13, 14, 15]

    def sum_for(question_numbers: list[int]) -> int:
        """
        Helper function that calculates total score for a given group of questions.
        It converts question numbers into a python list indexes and sums up responses
        """
        total = 0
        for qn in question_numbers:
            idx = qn - 1  # converts question number to index
            if 0 <= idx < len(answers):
                # adding anwser value to total score
                total += int(answers[idx])
        return total

    overload = sum_for(OVERLOAD_QS)
    invasion = sum_for(INVASION_QS)
    complexity = sum_for(COMPLEXITY_QS)

    return {
        "overload": overload,
        "invasion": invasion,
        "complexity": complexity
    }
