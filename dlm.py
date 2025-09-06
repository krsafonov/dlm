#!/usr/bin/env python3
"""
DLM (Download Library Manager) - CLI entry point for file organization.

Commands:
1. find-important - Find important files and save list to .dlm/important_files.txt
2. find-trash - Find trash files and save list to .dlm/trash_files.txt  
3. find-all - Run both find-important and find-trash
4. organize - Move files according to lists created by find commands
"""

import argparse
import json
import os
from pathlib import Path
from typing import List, Dict

from src.initial_sort import initial_analysis
from src.file_organizer import create_folders, move_files_to_dir, revert_moves


def ensure_dlm_dir(directory: str) -> Path:
    """Ensure .dlm directory exists in the given directory."""
    dlm_path = Path(directory) / ".dlm"
    dlm_path.mkdir(exist_ok=True)
    return dlm_path


def save_file_list(dlm_path: Path, filename: str, files: List[str]) -> None:
    """Save list of files to a text file in .dlm directory."""
    file_path = dlm_path / filename
    with open(file_path, 'w') as f:
        for file in files:
            f.write(f"{file}\n")
    print(f"Saved {len(files)} files to {file_path}")


def load_file_list(dlm_path: Path, filename: str) -> List[str]:
    """Load list of files from a text file in .dlm directory."""
    file_path = dlm_path / filename
    if not file_path.exists():
        return []
    
    with open(file_path, 'r') as f:
        files = [line.strip() for line in f if line.strip()]
    return files


def find_important_files(directory: str, batch_size: int = 100) -> None:
    """Find important files and save list to .dlm/important_files.txt"""
    dlm_path = ensure_dlm_dir(directory)
    important_file_path = dlm_path / "important_files.txt"
    
    # Check if file already exists
    if important_file_path.exists():
        existing_files = load_file_list(dlm_path, "important_files.txt")
        print(f"⚠️ Important files list already exists with {len(existing_files)} files.")
        response = input("Do you want to run the analysis again? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("Skipping important files analysis.")
            return
    
    print(f"🔍 Finding important files in {directory}...")
    
    # Run analysis
    results = initial_analysis(directory, batch_size, "important")
    
    if results["gemini_analysis"].get("error"):
        print(f"❌ Error: {results['gemini_analysis']['error']}")
        return
    
    # Extract important files
    important_files = []
    gemini_analysis = results["gemini_analysis"]
    
    if "file_analysis" in gemini_analysis:
        for file_info in gemini_analysis["file_analysis"]:
            if file_info.get("important", False):
                important_files.append(file_info["filename"])
    
    # Save to .dlm directory
    save_file_list(dlm_path, "important_files.txt", important_files)
    
    print(f"✅ Found {len(important_files)} important files")


def find_trash_files(directory: str, batch_size: int = 100) -> None:
    """Find trash files and save list to .dlm/trash_files.txt"""
    dlm_path = ensure_dlm_dir(directory)
    trash_file_path = dlm_path / "trash_files.txt"
    
    # Check if file already exists
    if trash_file_path.exists():
        existing_files = load_file_list(dlm_path, "trash_files.txt")
        print(f"⚠️ Trash files list already exists with {len(existing_files)} files.")
        response = input("Do you want to run the analysis again? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("Skipping trash files analysis.")
            return
    
    print(f"🗑️ Finding trash files in {directory}...")
    
    # Run analysis
    results = initial_analysis(directory, batch_size, "trash")
    
    if results["gemini_analysis"].get("error"):
        print(f"❌ Error: {results['gemini_analysis']['error']}")
        return
    
    # Extract trash files
    trash_files = []
    gemini_analysis = results["gemini_analysis"]
    
    if "file_analysis" in gemini_analysis:
        for file_info in gemini_analysis["file_analysis"]:
            if file_info.get("trash", False):
                trash_files.append(file_info["filename"])
    
    # Save to .dlm directory
    save_file_list(dlm_path, "trash_files.txt", trash_files)
    
    print(f"✅ Found {len(trash_files)} trash files")


def find_all_files(directory: str, batch_size: int = 100) -> None:
    """Run both find-important and find-trash"""
    print(f"🔍 Finding all files in {directory}...")
    find_important_files(directory, batch_size)
    find_trash_files(directory, batch_size)


def initial_organize_files(directory: str) -> None:
    """Move files according to lists created by find commands (initial organization)"""
    print(f"📁 Initial organization of files in {directory}...")
    
    dlm_path = ensure_dlm_dir(directory)
    
    # Load file lists
    important_files = load_file_list(dlm_path, "important_files.txt")
    trash_files = load_file_list(dlm_path, "trash_files.txt")
    
    if not important_files and not trash_files:
        print("❌ No file lists found. Run 'find-important' or 'find-trash' first.")
        return
    
    # Set up log file
    log_file = str(dlm_path / "move_log.json")
    
    # Create folders
    folders_to_create = []
    if important_files:
        folders_to_create.append("important")
    if trash_files:
        folders_to_create.append("trash")
    
    if folders_to_create:
        create_folders(directory, folders_to_create, log_file)
        print(f"📂 Created folders: {', '.join(folders_to_create)}")
    
    # Move files
    total_moved = 0
    
    if important_files:
        result = move_files_to_dir(directory, important_files, "important", log_file)
        moved_count = len(result["moves"])
        total_moved += moved_count
        print(f"✅ Moved {moved_count} important files to 'important/' folder")
        
        if result["errors"]:
            print(f"⚠️ Errors: {len(result['errors'])}")
    
    if trash_files:
        result = move_files_to_dir(directory, trash_files, "trash", log_file)
        moved_count = len(result["moves"])
        total_moved += moved_count
        print(f"✅ Moved {moved_count} trash files to 'trash/' folder")
        
        if result["errors"]:
            print(f"⚠️ Errors: {len(result['errors'])}")
    
    print(f"📊 Total files moved: {total_moved}")
    print(f"📝 Move log saved to: {log_file}")


def revert_organization(directory: str) -> None:
    """Revert initial organization using move log"""
    print(f"↩️ Reverting initial organization in {directory}...")
    
    dlm_path = ensure_dlm_dir(directory)
    log_file = dlm_path / "move_log.json"
    
    if not log_file.exists():
        print("❌ No move log found. Nothing to revert.")
        return
    
    result = revert_moves(str(log_file))
    
    print(f"✅ Reverted {len(result['reverted'])} files")
    print(f"✅ Removed {len(result['folders_removed'])} folders")
    
    if result["errors"]:
        print(f"⚠️ Errors: {len(result['errors'])}")
        for error in result["errors"]:
            print(f"  - {error}")
    
    if result["not_found"]:
        print(f"⚠️ Items not found: {len(result['not_found'])}")
        for not_found in result["not_found"]:
            print(f"  - {not_found}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="DLM - Download Library Manager for intelligent file organization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  find-important    Find important files and save list to .dlm/important_files.txt
  find-trash        Find trash files and save list to .dlm/trash_files.txt
  find-all          Run both find-important and find-trash
  initial-organize  Move files according to lists created by find commands (initial organization)
  revert            Revert initial organization using move log

Examples:
  dlm.py find-important ~/Downloads
  dlm.py find-trash ~/Downloads --batch-size 50
  dlm.py find-all ~/Downloads
  dlm.py initial-organize ~/Downloads
  dlm.py revert ~/Downloads
        """
    )
    
    parser.add_argument("command", 
                       choices=["find-important", "find-trash", "find-all", "initial-organize", "revert"],
                       help="Command to execute")
    parser.add_argument("directory", help="Directory to process")
    parser.add_argument("--batch-size", "-b", type=int, default=100,
                       help="Number of files to process in each batch (default: 100)")
    
    args = parser.parse_args()
    
    # Validate directory
    if not os.path.exists(args.directory):
        print(f"❌ Error: Directory '{args.directory}' does not exist")
        return 1
    
    if not os.path.isdir(args.directory):
        print(f"❌ Error: '{args.directory}' is not a directory")
        return 1
    
    try:
        if args.command == "find-important":
            find_important_files(args.directory, args.batch_size)
        elif args.command == "find-trash":
            find_trash_files(args.directory, args.batch_size)
        elif args.command == "find-all":
            find_all_files(args.directory, args.batch_size)
        elif args.command == "initial-organize":
            initial_organize_files(args.directory)
        elif args.command == "revert":
            revert_organization(args.directory)
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
