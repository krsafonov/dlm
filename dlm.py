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
from src.group_sort import group_analysis
from src.group_organizer import organize_by_groups, revert_group_organization


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
    group_log_file = dlm_path / "group_move_log.json"
    
    if not log_file.exists():
        if group_log_file.exists():
            print("❌ No initial organization move log found.")
            print("💡 Found group organization log. Use 'revert-groups' command instead.")
        else:
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


def find_groups(directory: str, batch_size: int = 100) -> None:
    """Find file groups for organization"""
    print(f"🔍 Finding file groups in {directory}...")
    
    results = group_analysis(directory, batch_size)
    
    if results.get("error"):
        print(f"❌ Error: {results['error']}")
        return
    
    groups = results.get("groups", [])
    print(f"✅ Found {len(groups)} groups")
    
    # Show summary
    for group in groups:
        suggested_folder = group.get('suggested_folder', 'keep in place')
        print(f"  📦 {group['group_name']}: {len(group['files'])} files → {suggested_folder}")


def organize_groups(directory: str) -> None:
    """Organize files according to group analysis"""
    print(f"📁 Organizing files by groups in {directory}...")
    
    results = organize_by_groups(directory)
    
    if results.get("error"):
        print(f"❌ Error: {results['error']}")
        return
    
    print(f"✅ Processed {results['groups_processed']} groups")
    print(f"✅ Moved {results['files_moved']} files")
    
    if results.get("errors"):
        print(f"⚠️ Errors: {len(results['errors'])}")
        for error in results["errors"]:
            print(f"  - {error}")


def revert_groups(directory: str) -> None:
    """Revert group organization"""
    print(f"↩️ Reverting group organization in {directory}...")
    
    # Check for helpful error messages
    dlm_path = ensure_dlm_dir(directory)
    log_file = dlm_path / "move_log.json"
    group_log_file = dlm_path / "group_move_log.json"
    
    if not group_log_file.exists():
        if log_file.exists():
            print("❌ No group organization move log found.")
            print("💡 Found initial organization log. Use 'revert' command instead.")
        else:
            print("❌ No group organization move log found. Nothing to revert.")
        return
    
    results = revert_group_organization(directory)
    
    if results.get("error"):
        print(f"❌ Error: {results['error']}")
        return
    
    print(f"✅ Reverted {len(results['reverted'])} files")
    print(f"✅ Removed {len(results['folders_removed'])} folders")
    
    if results["errors"]:
        print(f"⚠️ Errors: {len(results['errors'])}")
        for error in results["errors"]:
            print(f"  - {error}")
    
    if results["not_found"]:
        print(f"⚠️ Items not found: {len(results['not_found'])}")
        for not_found in results["not_found"]:
            print(f"  - {not_found}")


def organize_all(directory: str, batch_size: int = 100) -> None:
    """Run complete organization: find-all, initial-organize, find-groups, organize-groups"""
    print(f"🚀 Running complete organization in {directory}...")
    print("=" * 60)
    
    try:
        # Step 1: Find important and trash files
        print("📋 Step 1/4: Finding important and trash files...")
        find_all_files(directory, batch_size)
        print("✅ Step 1 complete!\n")
        
        # Step 2: Initial organization
        print("📁 Step 2/4: Initial organization...")
        initial_organize_files(directory)
        print("✅ Step 2 complete!\n")
        
        # Step 3: Find groups
        print("🔍 Step 3/4: Finding file groups...")
        find_groups(directory, batch_size)
        print("✅ Step 3 complete!\n")
        
        # Step 4: Organize groups
        print("📦 Step 4/4: Organizing groups...")
        organize_groups(directory)
        print("✅ Step 4 complete!\n")
        
        print("=" * 60)
        print("🎉 Complete organization finished successfully!")
        print("💡 Use 'revert-all' to undo all changes if needed.")
        
    except Exception as e:
        print(f"❌ Error during organization: {e}")
        print("💡 You can use 'revert-all' to undo any partial changes.")
        raise


def revert_all(directory: str) -> None:
    """Revert any organization (initial or groups)"""
    print(f"↩️ Reverting any organization in {directory}...")
    
    dlm_path = ensure_dlm_dir(directory)
    log_file = dlm_path / "move_log.json"
    group_log_file = dlm_path / "group_move_log.json"
    
    reverted_initial = False
    reverted_groups = False
    
    # Try to revert initial organization
    if log_file.exists():
        print("🔄 Reverting initial organization...")
        revert_organization(directory)
        reverted_initial = True
    
    # Try to revert group organization
    if group_log_file.exists():
        print("🔄 Reverting group organization...")
        revert_groups(directory)
        reverted_groups = True
    
    if not reverted_initial and not reverted_groups:
        print("❌ No organization logs found. Nothing to revert.")
    else:
        print("✅ Revert complete!")


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
  find-groups       Analyze files and identify groups for organization
  organize-groups   Organize files according to group analysis results
  revert-groups     Revert group organization using move log
  revert-all        Revert any organization (initial or groups)
  organize-all      Run complete organization (find-all + initial-organize + find-groups + organize-groups)

Examples:
  dlm.py find-important ~/Downloads
  dlm.py find-trash ~/Downloads --batch-size 50
  dlm.py find-all ~/Downloads
  dlm.py initial-organize ~/Downloads
  dlm.py revert ~/Downloads
  dlm.py find-groups ~/Downloads
  dlm.py organize-groups ~/Downloads
  dlm.py revert-groups ~/Downloads
  dlm.py revert-all ~/Downloads
  dlm.py organize-all ~/Downloads
        """
    )
    
    parser.add_argument("command", 
                       choices=["find-important", "find-trash", "find-all", "initial-organize", "revert", 
                               "find-groups", "organize-groups", "revert-groups", "revert-all", "organize-all"],
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
        elif args.command == "find-groups":
            find_groups(args.directory, args.batch_size)
        elif args.command == "organize-groups":
            organize_groups(args.directory)
        elif args.command == "revert-groups":
            revert_groups(args.directory)
        elif args.command == "revert-all":
            revert_all(args.directory)
        elif args.command == "organize-all":
            organize_all(args.directory, args.batch_size)
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
