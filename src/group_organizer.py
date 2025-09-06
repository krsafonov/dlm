#!/usr/bin/env python3
"""
Group organizer utility that:
1. Loads group analysis results from .dlm/groups.json
2. Creates suggested folder structure
3. Moves files according to group suggestions
4. Provides revert capability
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List
from datetime import datetime

from src.file_organizer import create_folders, move_files_to_dir, revert_moves


def load_group_analysis(directory: str) -> List[Dict]:
    """
    Load group analysis results from .dlm/groups.json.
    
    Args:
        directory: Base directory containing .dlm folder
        
    Returns:
        List of group analysis results
    """
    groups_file = Path(directory) / ".dlm" / "groups.json"
    
    if not groups_file.exists():
        raise FileNotFoundError(f"Group analysis not found: {groups_file}")
    
    with open(groups_file, 'r') as f:
        groups = json.load(f)
    
    return groups


def get_suggested_folders(groups: List[Dict]) -> List[str]:
    """
    Extract unique suggested folders from group analysis.
    
    Args:
        groups: List of group analysis results
        
    Returns:
        List of unique folder names
    """
    folders = set()
    
    for group in groups:
        suggested_folder = group.get('suggested_folder')
        if suggested_folder:
            # Extract folder name from path
            folder_name = Path(suggested_folder).name
            folders.add(folder_name)
    
    return sorted(list(folders))


def organize_by_groups(directory: str, log_file: str = None) -> Dict:
    """
    Organize files according to group analysis results.
    
    Args:
        directory: Base directory to organize
        log_file: Optional log file for tracking moves
        
    Returns:
        Dictionary with organization results
    """
    print(f"📁 Organizing files by groups in: {directory}")
    
    # Load group analysis
    try:
        groups = load_group_analysis(directory)
    except FileNotFoundError as e:
        return {"error": str(e)}
    
    if not groups:
        return {"error": "No groups found in analysis"}
    
    # Set up log file
    if not log_file:
        dlm_path = Path(directory) / ".dlm"
        log_file = str(dlm_path / "group_move_log.json")
    
    # Get suggested folders
    suggested_folders = get_suggested_folders(groups)
    
    if suggested_folders:
        print(f"📂 Creating folders: {', '.join(suggested_folders)}")
        create_folders(directory, suggested_folders, log_file)
    
    # Organize files by groups
    results = {
        "groups_processed": 0,
        "files_moved": 0,
        "errors": []
    }
    
    for group in groups:
        group_name = group['group_name']
        files = group['files']
        suggested_folder = group.get('suggested_folder')
        
        print(f"\n📦 Processing group: {group_name}")
        print(f"   Files: {len(files)}")
        
        if suggested_folder:
            # Move to suggested folder
            folder_name = Path(suggested_folder).name
            print(f"   Target folder: {folder_name}")
            result = move_files_to_dir(directory, files, folder_name, log_file)
            results["files_moved"] += len(result["moves"])
            results["groups_processed"] += 1
            
            if result["errors"]:
                results["errors"].extend(result["errors"])
        else:
            print(f"   ⏭️ No target folder specified, keeping files in place")
            results["groups_processed"] += 1
    
    results["log_file"] = log_file
    return results


def revert_group_organization(directory: str) -> Dict:
    """
    Revert group organization using move log and clear the log.
    
    Args:
        directory: Base directory
        
    Returns:
        Dictionary with revert results
    """
    print(f"↩️ Reverting group organization in: {directory}")
    
    dlm_path = Path(directory) / ".dlm"
    log_file = dlm_path / "group_move_log.json"
    
    if not log_file.exists():
        return {"error": "No group move log found. Nothing to revert."}
    
    # Revert the moves
    result = revert_moves(str(log_file))
    
    # Clear the move log after successful revert
    if not result.get("error"):
        try:
            log_file.unlink()
            print(f"🗑️ Cleared move log: {log_file}")
        except Exception as e:
            print(f"⚠️ Warning: Could not clear move log: {e}")
    
    return result


