from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List

# ---------------- OOPS Classes -----------------

class Question:
    def __init__(self, text, points):
        self.text = text
        self.points = points

    def check_answer(self, answer):
        raise NotImplementedError  # polymorphism


class SingleChoiceQuestion(Question):
    def __init__(self, text, options, correct_answer, points=1):
        super().__init__(text, points)
        self.options = options
        self.correct_answer = correct_answer

    def check_answer(self, answer):
        return self.points if answer == self.correct_answer else 0


class MultiSelectQuestion(Question):
    def __init__(self, text, options, correct_answers: List[str], points=2):
        super().__init__(text, points)
        self.options = options
        self.correct_answers = correct_answers

    def check_answer(self, answers):
        return self.points if set(answers) == set(self.correct_answers) else 0


class FillBlankQuestion(Question):
    def __init__(self, text, correct_answer, points=1):
        super().__init__(text, points)
        self.correct_answer = correct_answer.lower()

    def check_answer(self, answer):
        return self.points if answer.lower() == self.correct_answer else 0


# ----------------- FastAPI App -------------------

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Quiz Data
quiz = [
    SingleChoiceQuestion("What is the capital of France?", ["Paris", "London", "Berlin"], "Paris"),
    MultiSelectQuestion("Select prime numbers", ["2", "3", "4", "5"], ["2", "3", "5"]),
    FillBlankQuestion("Fill in the blank: FastAPI is built on _____?", "Starlette")
]

user_answers = {}
current_question = 0


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/question/{qid}")
def get_question(request: Request, qid: int):
    if qid >= len(quiz):
        return RedirectResponse(url="/result")

    question = quiz[qid]
    return templates.TemplateResponse("question.html", {
        "request": request,
        "question": question,
        "qid": qid
    })


@app.post("/answer/{qid}")
def submit_answer(qid: int, answer: str = Form(None), multi_answer: List[str] = Form(None), fill: str = Form(None)):
    question = quiz[qid]

    if isinstance(question, SingleChoiceQuestion):
        user_answers[qid] = question.check_answer(answer)

    elif isinstance(question, MultiSelectQuestion):
        user_answers[qid] = question.check_answer(multi_answer or [])

    elif isinstance(question, FillBlankQuestion):
        user_answers[qid] = question.check_answer(fill or "")

    return RedirectResponse(url=f"/question/{qid+1}", status_code=303)


@app.get("/result")
def result(request: Request):
    score = sum(user_answers.values())
    return templates.TemplateResponse("result.html", {"request": request, "score": score, "total": sum(q.points for q in quiz)})
