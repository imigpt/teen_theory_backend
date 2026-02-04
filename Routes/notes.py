from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from db.database import notes, get_user_collection
from models.notes_model import NoteModel, NoteUpdateModel
from typing import List
from datetime import datetime
from bson.objectid import ObjectId

notes_router = APIRouter(prefix="/notes", tags=["Notes"])
security = HTTPBearer()


@notes_router.post("/create", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_note(
    note_data: NoteModel,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Create a new note. created_by_user_email is set from the token."""
    token = credentials.credentials
    user_collection = get_user_collection()
    notes_collection = notes()

    # Verify user by token
    user = user_collection.find_one({"token": token})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    created_by_email = user.get("email")

    # Create note document
    note_doc = {
        "project_name": note_data.project_name,
        "created_by_user_email": created_by_email,
        "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "notes": note_data.notes,
    }

    result = notes_collection.insert_one(note_doc)
    note_doc["_id"] = str(result.inserted_id)

    return {
        "success": True,
        "message": "Note created successfully",
        "data": note_doc,
    }


@notes_router.get("/all", response_model=dict, status_code=status.HTTP_200_OK)
async def get_all_notes(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Get all notes from all users."""
    token = credentials.credentials
    user_collection = get_user_collection()
    notes_collection = notes()

    # Verify user by token
    user = user_collection.find_one({"token": token})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    # Fetch all notes
    all_notes = list(notes_collection.find({}))
    
    # Convert ObjectId to string
    for note in all_notes:
        note["_id"] = str(note["_id"])

    return {
        "success": True,
        "message": "All notes retrieved successfully",
        "count": len(all_notes),
        "data": all_notes,
    }


@notes_router.get("/my-notes", response_model=dict, status_code=status.HTTP_200_OK)
async def get_my_notes(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Get notes created by the authenticated user (filtered by token)."""
    token = credentials.credentials
    user_collection = get_user_collection()
    notes_collection = notes()

    # Verify user by token
    user = user_collection.find_one({"token": token})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    created_by_email = user.get("email")

    # Fetch notes created by this user
    user_notes = list(notes_collection.find({"created_by_user_email": created_by_email}))
    
    # Convert ObjectId to string
    for note in user_notes:
        note["_id"] = str(note["_id"])

    return {
        "success": True,
        "message": "Your notes retrieved successfully",
        "count": len(user_notes),
        "data": user_notes,
    }


@notes_router.put("/update/{note_id}", response_model=dict, status_code=status.HTTP_200_OK)
async def update_note(
    note_id: str,
    update_data: NoteUpdateModel,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Update a note. Only the creator can update their note."""
    token = credentials.credentials
    user_collection = get_user_collection()
    notes_collection = notes()

    # Verify user by token
    user = user_collection.find_one({"token": token})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    created_by_email = user.get("email")

    # Validate note_id
    try:
        object_id = ObjectId(note_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid note ID format"
        )

    # Find the note
    note = notes_collection.find_one({"_id": object_id})
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )

    # Verify that the user is the creator
    if note.get("created_by_user_email") != created_by_email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own notes"
        )

    # Prepare update data (only include non-None fields)
    update_fields = {}
    if update_data.project_name is not None:
        update_fields["project_name"] = update_data.project_name
    if update_data.notes is not None:
        update_fields["notes"] = update_data.notes

    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    # Update the note
    notes_collection.update_one(
        {"_id": object_id},
        {"$set": update_fields}
    )

    # Get updated note
    updated_note = notes_collection.find_one({"_id": object_id})
    updated_note["_id"] = str(updated_note["_id"])

    return {
        "success": True,
        "message": "Note updated successfully",
        "data": updated_note,
    }


@notes_router.delete("/delete/{note_id}", response_model=dict, status_code=status.HTTP_200_OK)
async def delete_note(
    note_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Delete a note. Only the creator can delete their note."""
    token = credentials.credentials
    user_collection = get_user_collection()
    notes_collection = notes()

    # Verify user by token
    user = user_collection.find_one({"token": token})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    created_by_email = user.get("email")

    # Validate note_id
    try:
        object_id = ObjectId(note_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid note ID format"
        )

    # Find the note
    note = notes_collection.find_one({"_id": object_id})
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )

    # Verify that the user is the creator
    if note.get("created_by_user_email") != created_by_email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own notes"
        )

    # Delete the note
    notes_collection.delete_one({"_id": object_id})

    return {
        "success": True,
        "message": "Note deleted successfully",
        "data": {
            "_id": note_id,
            "deleted": True
        }
    }
