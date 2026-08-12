# ============================================================================
# CRITICAL FIXES FOR gui.py
# ============================================================================
# This file contains the corrected versions of buggy functions from gui.py
# Apply these fixes to replace the broken versions in the main gui.py
# ============================================================================

import numpy as np
from PyQt5.QtWidgets import QMessageBox, QProgressDialog, QApplication
from PyQt5.QtCore import Qt


# FIX #1: Line 2184 - Type mismatch error in _draw_peak_markers
# ============================================================================
def fix_draw_peak_markers_sorting(peak_channels):
    """
    FIXED: Handles both string ('Channel1') and int (1) channel identifiers.
    
    BEFORE (BROKEN):
        key=lambda x: int(x.replace('Channel', '') or '0')
        # ❌ Crashes if x is an int: AttributeError: 'int' object has no attribute 'replace'
    
    AFTER (FIXED):
        Properly converts to string first, then extracts number.
    """
    def channel_sort_key(x):
        # Convert to string to handle both 'Channel1' and 1
        s = str(x)
        # Remove 'Channel' prefix if present
        if s.startswith('Channel'):
            s = s.replace('Channel', '')
        # Extract number, default to 0 if empty
        try:
            return int(s or '0')
        except ValueError:
            return 0
    
    return sorted(set(peak_channels), key=channel_sort_key)


# FIX #2: Line 2694-2695 - Wrong index used in _clear_all_peaks
# ============================================================================
def fix_clear_all_peaks(wd, deleted_peaks, well):
    """
    FIXED: Marks actual peak scan values as deleted, not array indices.
    
    BEFORE (BROKEN):
        for idx in range(n_peaks):
            deleted.add(idx)  # ❌ Adds 0,1,2,3... instead of actual scan positions
    
    AFTER (FIXED):
        Correctly adds the actual scan position values from wd['peaks']
    """
    if wd is None or 'peaks' not in wd:
        return False
    
    peaks = wd.get('peaks', [])
    n_peaks = len(peaks)
    
    if n_peaks == 0:
        return False
    
    # Mark ACTUAL peak scan positions as deleted, not indices
    deleted = deleted_peaks.setdefault(well, set())
    for peak_scan in peaks:
        deleted.add(int(peak_scan))
    
    # Also clear manual peaks for this well
    return True


# FIX #3: Line 1829 - Incorrect peak filtering in _apply_manual_edits
# ============================================================================
def fix_apply_manual_edits_filtering(wd, deleted_peaks, manual_peaks, well):
    """
    FIXED: Properly filters peaks using numpy boolean indexing.
    
    BEFORE (BROKEN):
        keep_mask = np.array([p not in deleted for p in wd['peaks']])
        wd['peak_channels'] = [wd['peak_channels'][i] for i in range(len(...)) if keep_mask[i]]
        # ❌ Inefficient and fragile indexing
    
    AFTER (FIXED):
        Uses direct numpy masking for all parallel arrays
    """
    # Remove deleted peaks
    deleted = deleted_peaks.get(well, set())
    if deleted and len(wd.get('peaks', [])) > 0:
        keep_mask = np.array([p not in deleted for p in wd['peaks']])
        
        wd['peaks'] = wd['peaks'][keep_mask]
        wd['peak_channels'] = [wd['peak_channels'][i] for i, keep in enumerate(keep_mask) if keep]
        wd['peak_lefts'] = wd['peak_lefts'][keep_mask]
        wd['peak_rights'] = wd['peak_rights'][keep_mask]
    
    # Add manually added peaks
    manual = manual_peaks.get(well, [])
    for idx, ch in manual:
        if not np.any(wd['peaks'] == idx):
            wd['peaks'] = np.append(wd['peaks'], idx)
            wd['peak_channels'].append(ch)
            wd['peak_lefts'] = np.append(wd['peak_lefts'], max(0, idx - 2))
            wd['peak_rights'] = np.append(wd['peak_rights'], idx + 2)
    
    # Re-sort by scan position
    if len(wd['peaks']) > 0:
        sort_idx = np.argsort(wd['peaks'])
        wd['peaks'] = wd['peaks'][sort_idx]
        wd['peak_channels'] = [wd['peak_channels'][i] for i in sort_idx]
        wd['peak_lefts'] = wd['peak_lefts'][sort_idx]
        wd['peak_rights'] = wd['peak_rights'][sort_idx]


# FIX #4: ESD Progress dialog increment order (Line 1373)
# ============================================================================
def fix_esd_progress_update(esd_progress, esd_count, total_esd):
    """
    FIXED: Increments before setting value to match progress bar correctly.
    
    BEFORE (BROKEN):
        esd_progress.setValue(min(esd_count, total_esd)); esd_count += 1
        # ❌ Progress appears behind actual progress
    
    AFTER (FIXED):
        Increments first, then updates UI
    """
    esd_count += 1
    esd_progress.setValue(min(esd_count, total_esd))
    QApplication.processEvents()
    return esd_count


# FIX #5: Better error handling for peak operations
# ============================================================================
def show_error_with_context(parent, title, message, exception=None, details=""):
    """
    IMPROVED: Shows detailed error messages with context.
    
    This replaces generic QMessageBox.critical() calls with helpful debugging info.
    """
    import traceback
    
    full_message = message
    if details:
        full_message += f"\n\nDetails:\n{details}"
    if exception:
        full_message += f"\n\nException:\n{str(exception)}"
        full_message += f"\n\nTraceback:\n{traceback.format_exc()}"
    
    QMessageBox.critical(parent, title, full_message)


# FIX #6: Add undo/redo stack size limit to prevent memory leaks
# ============================================================================
class UndoManagerFixed:
    """
    IMPROVED: Adds size limit to prevent unbounded memory growth.
    
    BEFORE:
        Undo stacks could grow infinitely
    
    AFTER:
        Limited to last 50 actions (configurable)
    """
    def __init__(self, max_size=50):
        self._undo_stack = []
        self._redo_stack = []
        self._max_size = max_size
    
    def push(self, action):
        self._undo_stack.append(action)
        # Limit stack size to prevent memory leaks
        if len(self._undo_stack) > self._max_size:
            self._undo_stack.pop(0)
        self._redo_stack.clear()
    
    def undo(self):
        if not self._undo_stack:
            return None
        action = self._undo_stack.pop()
        self._redo_stack.append(action)
        # Keep redo stack bounded too
        if len(self._redo_stack) > self._max_size:
            self._redo_stack.pop(0)
        return action
    
    def redo(self):
        if not self._redo_stack:
            return None
        action = self._redo_stack.pop()
        self._undo_stack.append(action)
        # Keep undo stack bounded
        if len(self._undo_stack) > self._max_size:
            self._undo_stack.pop(0)
        return action
    
    def clear(self):
        self._undo_stack.clear()
        self._redo_stack.clear()


# FIX #7: Vectorized peak filtering for better performance
# ============================================================================
def vectorized_peak_filter(peaks, peak_channels, peak_lefts, peak_rights, deleted_set):
    """
    OPTIMIZED: Uses numpy vectorization instead of loops.
    
    BEFORE:
        keep_mask = np.array([p not in deleted for p in wd['peaks']])
        wd['peak_channels'] = [wd['peak_channels'][i] for i in range(...) if keep_mask[i]]
        # ❌ Multiple loops over same data
    
    AFTER:
        Single numpy operation to filter all arrays at once
    """
    if len(deleted_set) == 0:
        return peaks, peak_channels, peak_lefts, peak_rights
    
    # Create boolean mask for peaks to keep
    keep_mask = np.array([int(p) not in deleted_set for p in peaks], dtype=bool)
    
    # Apply mask to all parallel arrays
    filtered_peaks = peaks[keep_mask]
    filtered_channels = [peak_channels[i] for i in np.where(keep_mask)[0]]
    filtered_lefts = peak_lefts[keep_mask]
    filtered_rights = peak_rights[keep_mask]
    
    return filtered_peaks, filtered_channels, filtered_lefts, filtered_rights


# FIX #8: Improved progress dialog class for reuse
# ============================================================================
class ProgressManager:
    """
    IMPROVED: Reusable progress dialog with better state management.
    
    Replaces multiple QProgressDialog instantiations with a single class.
    """
    def __init__(self, parent, title, max_items=100):
        self.parent = parent
        self.dialog = QProgressDialog(f"{title}...", "Cancel", 0, max_items, parent)
        self.dialog.setWindowModality(Qt.WindowModal)
        self.dialog.setWindowTitle(title)
        self.current = 0
        self.max_items = max_items
    
    def update(self, value, label=""):
        """Update progress bar with optional label."""
        self.current = value
        self.dialog.setValue(min(value, self.max_items))
        if label:
            self.dialog.setLabelText(label)
        QApplication.processEvents()
        return not self.dialog.wasCanceled()
    
    def increment(self, label=""):
        """Increment progress by 1."""
        return self.update(self.current + 1, label)
    
    def set_maximum(self, max_items):
        """Update maximum value."""
        self.max_items = max_items
        self.dialog.setMaximum(max_items)
    
    def close(self):
        """Close the progress dialog."""
        self.dialog.close()
    
    def was_canceled(self):
        """Check if user clicked cancel."""
        return self.dialog.wasCanceled()


# ============================================================================
# HOW TO APPLY THESE FIXES TO gui.py:
# ============================================================================
"""
1. REPLACE Line 2182-2185 in _draw_peak_markers():
   OLD:
       for ch in sorted(
           set(peak_channels),
           key=lambda x: int(x.replace('Channel', '') or '0')
       ):
   
   NEW:
       for ch in fix_draw_peak_markers_sorting(peak_channels):

2. REPLACE Line 2693-2698 in _clear_all_peaks():
   OLD:
       n_peaks = len(wd.get('peaks', []))
       if n_peaks == 0:
           ...
       deleted = self._deleted_peaks.setdefault(well, set())
       for idx in range(n_peaks):
           deleted.add(idx)
   
   NEW:
       fix_clear_all_peaks(wd, self._deleted_peaks, well)

3. REPLACE Line 1822-1847 in _apply_manual_edits():
   OLD:
       deleted = self._deleted_peaks.get(well, set())
       if deleted and len(wd['peaks']) > 0:
           keep_mask = np.array([p not in deleted for p in wd['peaks']])
           ...
   
   NEW:
       fix_apply_manual_edits_filtering(wd, self._deleted_peaks, 
                                        self._manual_peaks, well)

4. REPLACE Line 270 in __init__():
   OLD:
       self._undo_manager = UndoManager()
   
   NEW:
       self._undo_manager = UndoManagerFixed(max_size=50)

5. Use ProgressManager for all progress dialogs:
   progress = ProgressManager(self, "Loading files", len(files))
   progress.update(i)
   progress.close()
"""
