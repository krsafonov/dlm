#!/usr/bin/env python3
"""
File organization library that provides:
1. Function to create folders with given names
2. Function to move files to specified directories
3. Function to revert moves based on move commands
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime


def create_folders(base_dir: str, folder_names: List[str], log_file: str = None) -> Dict[str, Path]:
    """
    Create folders with given names in the base directory.
    
    Args:
        base_dir: Base directory where folders will be created
        folder_names: List of folder names to create
        log_file: Optional log file for tracking folder creation
        
    Returns:
        Dictionary mapping folder names to folder paths
    """
    base_path = Path(base_dir)
    folders = {}
    created_folders = []
    
    for folder_name in folder_names:
        folder_path = base_path / folder_name
        if not folder_path.exists():
            folder_path.mkdir(exist_ok=True)
            created_folders.append(folder_name)
        folders[folder_name] = folder_path
    
    # Log folder creation if requested
    if log_file and created_folders:
        try:
            # Try to load existing log data
            existing_data = {"folders_created": []}
            if Path(log_file).exists():
                try:
                    with open(log_file, 'r') as f:
                        existing_data = json.load(f)
                except:
                    pass
            
            # Add new folder creation entries
            for folder_name in created_folders:
                folder_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "action": "create_folder",
                    "folder_name": folder_name,
                    "folder_path": str(folders[folder_name])
                }
                existing_data["folders_created"].append(folder_entry)
            
            # Save updated log
            with open(log_file, 'w') as f:
                json.dump(existing_data, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Failed to log folder creation: {e}")
    
    return folders


def move_files_to_dir(
    base_dir: str, 
    files: List[str], 
    target_dir: str,
    log_file: str = None
) -> Dict:
    """
    Move files from base directory to target directory.
    
    Args:
        base_dir: Base directory containing the files
        files: List of filenames to move
        target_dir: Target directory name (relative to base_dir)
        log_file: Path to log file for tracking moves (optional)
        
    Returns:
        Dictionary with move results and log data
    """
    base_path = Path(base_dir)
    target_path = base_path / target_dir
    
    # Create target directory if it doesn't exist
    target_path.mkdir(exist_ok=True)
    
    move_log = []
    results = {
        "moves": [],
        "errors": []
    }
    
    for filename in files:
        source_path = base_path / filename
        target_file_path = target_path / filename
        
        try:
            if source_path.exists():
                # Check if target already exists
                if target_file_path.exists():
                    # Create unique name
                    counter = 1
                    name_parts = target_file_path.stem, target_file_path.suffix
                    while target_file_path.exists():
                        new_name = f"{name_parts[0]}_{counter}{name_parts[1]}"
                        target_file_path = target_path / new_name
                        counter += 1
                
                # Move the file
                shutil.move(str(source_path), str(target_file_path))
                
                # Log the move
                move_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "source": str(source_path),
                    "target": str(target_file_path),
                    "filename": filename
                }
                move_log.append(move_entry)
                results["moves"].append(move_entry)
                
            else:
                error_msg = f"Source file not found: {filename}"
                results["errors"].append(error_msg)
                
        except Exception as e:
            error_msg = f"Failed to move {filename}: {str(e)}"
            results["errors"].append(error_msg)
    
    # Save move log if requested
    if log_file:
        try:
            # Try to load existing log data
            existing_data = {"moves": [], "folders_created": []}
            if Path(log_file).exists():
                try:
                    with open(log_file, 'r') as f:
                        existing_data = json.load(f)
                except:
                    pass
            
            # Combine existing moves with new moves
            all_moves = existing_data.get("moves", []) + move_log
            
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "base_directory": str(base_path),
                "total_moves": len(all_moves),
                "moves": all_moves,
                "folders_created": existing_data.get("folders_created", [])
            }
            
            with open(log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
            
            results["log_file"] = log_file
            
        except Exception as e:
            error_msg = f"Failed to save log file: {str(e)}"
            results["errors"].append(error_msg)
    
    return results


def revert_moves(log_file: str) -> Dict:
    """
    Revert file moves and remove created folders based on a move log.
    
    Args:
        log_file: Path to the move log file
        
    Returns:
        Dictionary with revert results
    """
    results = {
        "reverted": [],
        "folders_removed": [],
        "errors": [],
        "not_found": []
    }
    
    try:
        with open(log_file, 'r') as f:
            log_data = json.load(f)
    except Exception as e:
        results["errors"].append(f"Failed to read log file: {str(e)}")
        return results
    
    moves = log_data.get("moves", [])
    folders_created = log_data.get("folders_created", [])
    
    if not moves and not folders_created:
        results["errors"].append("No moves or folder creation found in log file")
        return results
    
    # First, revert file moves
    if moves:
        # Sort moves in reverse order (most recent first) to avoid conflicts
        moves.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        for move in moves:
            source_path = Path(move["source"])
            target_path = Path(move["target"])
            
            try:
                if target_path.exists():
                    # Create parent directory if it doesn't exist
                    source_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Move file back
                    shutil.move(str(target_path), str(source_path))
                    results["reverted"].append(f"{target_path} -> {source_path}")
                else:
                    error_msg = f"Target file not found: {target_path}"
                    results["not_found"].append(error_msg)
                    
            except Exception as e:
                error_msg = f"Failed to revert {target_path}: {str(e)}"
                results["errors"].append(error_msg)
    
    # Then, remove created folders (in reverse order)
    if folders_created:
        # Sort folders by timestamp (most recent first) to remove in reverse order
        folders_created.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        for folder_entry in folders_created:
            folder_path = Path(folder_entry["folder_path"])
            
            try:
                if folder_path.exists() and folder_path.is_dir():
                    # Check if folder is empty
                    if not any(folder_path.iterdir()):
                        folder_path.rmdir()
                        results["folders_removed"].append(str(folder_path))
                    else:
                        error_msg = f"Folder not empty, cannot remove: {folder_path}"
                        results["errors"].append(error_msg)
                else:
                    error_msg = f"Folder not found or not a directory: {folder_path}"
                    results["not_found"].append(error_msg)
                    
            except Exception as e:
                error_msg = f"Failed to remove folder {folder_path}: {str(e)}"
                results["errors"].append(error_msg)
    
    return results
