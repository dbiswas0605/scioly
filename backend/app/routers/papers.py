"""Routes for listing, fetching, uploading, parsing, and publishing
QuestionPapers.

Upload just stores the raw file as a 'draft' paper. Parsing (turning that
file into questions/options via the active LLM provider) and publishing
(making a paper visible to students once every question has been reviewed)
are separate steps a parent/teacher drives from the upload review screen.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.crud import question_papers as papers_crud
from app.crud import questions as questions_crud
from app.crud import subjects as subjects_crud
from app.deps import get_db
from app.schemas.question_paper import QuestionPaperRead, QuestionPaperWithSubjectRead
from app.services.llm.dispatcher import parse_paper_with_llm
from app.services.llm.errors import LlmNotConfiguredError, LlmRequestError, LlmUnsupportedError

router = APIRouter(prefix="/papers", tags=["papers"])


@router.get("", response_model=list[QuestionPaperWithSubjectRead])
def list_papers(db: Session = Depends(get_db)) -> list[QuestionPaperWithSubjectRead]:
    rows = papers_crud.list_papers(db)
    return [
        QuestionPaperWithSubjectRead(
            **QuestionPaperRead.model_validate(paper).model_dump(),
            subject_name=subject_name,
        )
        for paper, subject_name in rows
    ]


@router.get("/{paper_id}", response_model=QuestionPaperRead)
def get_paper(paper_id: uuid.UUID, db: Session = Depends(get_db)) -> QuestionPaperRead:
    paper = papers_crud.get_paper_by_id(db, paper_id)
    if paper is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Question paper not found."
        )
    return paper


@router.post(
    "/upload", response_model=QuestionPaperRead, status_code=status.HTTP_201_CREATED
)
async def upload_paper(
    subject_id: uuid.UUID = Form(...),
    title: str = Form(...),
    description: str | None = Form(None),
    created_by: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> QuestionPaperRead:
    subject = subjects_crud.get_subject_by_id(db, subject_id)
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found."
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty."
        )

    paper = papers_crud.create_paper(
        db,
        subject_id=subject_id,
        title=title,
        source_filename=file.filename or "upload",
        source_content_type=file.content_type or "application/octet-stream",
        source_file=file_bytes,
        description=description,
        created_by=created_by,
    )
    return paper


@router.post("/{paper_id}/parse", response_model=QuestionPaperRead)
def parse_paper(paper_id: uuid.UUID, db: Session = Depends(get_db)) -> QuestionPaperRead:
    """Send the paper's uploaded file to the active LLM provider, extract
    questions/options from the response, and replace any existing questions
    for this paper with the freshly parsed ones (all unreviewed)."""
    paper = papers_crud.get_paper_by_id(db, paper_id)
    if paper is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Question paper not found."
        )

    try:
        parsed_questions = parse_paper_with_llm(db, paper)
    except LlmNotConfiguredError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except LlmUnsupportedError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except LlmRequestError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    questions_crud.replace_questions_for_paper(db, paper_id, parsed_questions)
    paper = papers_crud.set_status_and_question_count(
        db, paper, status="pending_review", total_questions=len(parsed_questions)
    )
    return paper


@router.post("/{paper_id}/publish", response_model=QuestionPaperRead)
def publish_paper(paper_id: uuid.UUID, db: Session = Depends(get_db)) -> QuestionPaperRead:
    """Make a paper visible to students. Requires every question to have
    been reviewed (confirmed or edited) by a parent/teacher first."""
    paper = papers_crud.get_paper_by_id(db, paper_id)
    if paper is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Question paper not found."
        )
    if paper.total_questions == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This paper has no questions yet — parse it first.",
        )

    unreviewed = questions_crud.count_unreviewed_questions(db, paper_id)
    if unreviewed > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{unreviewed} question(s) still need review before publishing.",
        )

    missing_answers = questions_crud.list_mcq_question_numbers_missing_correct_answer(
        db, paper_id
    )
    if missing_answers:
        numbers = ", ".join(str(n) for n in missing_answers)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Question(s) {numbers} need a correct answer marked before publishing.",
        )

    return papers_crud.set_status(db, paper, "published")


@router.delete("/{paper_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_paper(paper_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    """Delete a question paper (draft, pending_review, published, or
    archived) along with its questions and any student attempt history —
    used by Admin's Question Papers management screen."""
    paper = papers_crud.get_paper_by_id(db, paper_id)
    if paper is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Question paper not found."
        )
    papers_crud.delete_paper(db, paper)
