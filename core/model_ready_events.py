"""
Model Ready Event System
Provides proper model loading state management with events
"""

import threading
import time
from typing import Callable, Optional, Dict, Any
from enum import Enum


class ModelState(Enum):
    """Model loading states"""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"
    SHUTDOWN = "shutdown"


class ModelReadyEventManager:
    """
    Manages model ready events and state synchronization.
    Provides thread-safe model state management.
    """
    
    def __init__(self):
        # Threading events
        self.model_ready_event = threading.Event()
        self.initialization_lock = threading.Lock()
        
        # State management
        self.current_state = ModelState.UNINITIALIZED
        self.state_lock = threading.Lock()
        
        # Callbacks
        self.state_change_callbacks: Dict[ModelState, list] = {
            state: [] for state in ModelState
        }
        
        # Timing
        self.initialization_start_time: Optional[float] = None
        self.initialization_duration: Optional[float] = None
        
        # Error information
        self.last_error: Optional[Exception] = None
    
    def add_state_callback(self, state: ModelState, callback: Callable[[], None]):
        """Add callback for specific model state"""
        with self.state_lock:
            self.state_change_callbacks[state].append(callback)
    
    def remove_state_callback(self, state: ModelState, callback: Callable[[], None]):
        """Remove callback for specific model state"""
        with self.state_lock:
            if callback in self.state_change_callbacks[state]:
                self.state_change_callbacks[state].remove(callback)
    
    def _set_state(self, new_state: ModelState, error: Optional[Exception] = None):
        """Internal state change with callback execution"""
        with self.state_lock:
            old_state = self.current_state
            self.current_state = new_state
            
            if error:
                self.last_error = error
            
            # Calculate initialization duration
            if new_state == ModelState.READY and self.initialization_start_time:
                self.initialization_duration = time.time() - self.initialization_start_time
            
            print(f"Model state: {old_state.value} -> {new_state.value}")
            
            # Execute callbacks for this state
            callbacks = self.state_change_callbacks[new_state].copy()
        
        # Execute callbacks outside of lock to prevent deadlocks
        for callback in callbacks:
            try:
                callback()
            except Exception as e:
                print(f"State callback error: {e}")
    
    def start_initialization(self):
        """Mark model initialization as started"""
        if self.current_state == ModelState.INITIALIZING:
            return  # Already initializing
        
        with self.initialization_lock:
            self._set_state(ModelState.INITIALIZING)
            self.model_ready_event.clear()
            self.initialization_start_time = time.time()
            self.last_error = None
    
    def mark_ready(self):
        """Mark model as ready and signal waiting threads"""
        with self.initialization_lock:
            self._set_state(ModelState.READY)
            self.model_ready_event.set()
    
    def mark_error(self, error: Exception):
        """Mark model initialization as failed"""
        with self.initialization_lock:
            self._set_state(ModelState.ERROR, error)
            # Don't set the event - model is not ready
    
    def mark_shutdown(self):
        """Mark model as shutdown"""
        with self.initialization_lock:
            self._set_state(ModelState.SHUTDOWN)
            self.model_ready_event.clear()
    
    def wait_for_ready(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for model to be ready.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if model is ready, False if timeout or error
        """
        if self.current_state == ModelState.READY:
            return True
        
        if self.current_state == ModelState.ERROR:
            return False
        
        return self.model_ready_event.wait(timeout)
    
    def is_ready(self) -> bool:
        """Check if model is ready (non-blocking)"""
        return self.current_state == ModelState.READY
    
    def is_initializing(self) -> bool:
        """Check if model is initializing"""
        return self.current_state == ModelState.INITIALIZING
    
    def has_error(self) -> bool:
        """Check if model has error"""
        return self.current_state == ModelState.ERROR
    
    def get_state(self) -> ModelState:
        """Get current model state"""
        return self.current_state
    
    def get_last_error(self) -> Optional[Exception]:
        """Get last error if any"""
        return self.last_error
    
    def get_initialization_duration(self) -> Optional[float]:
        """Get initialization duration in seconds"""
        return self.initialization_duration
    
    def reset(self):
        """Reset to uninitialized state"""
        with self.initialization_lock:
            self._set_state(ModelState.UNINITIALIZED)
            self.model_ready_event.clear()
            self.initialization_start_time = None
            self.initialization_duration = None
            self.last_error = None
    
    def get_status_info(self) -> Dict[str, Any]:
        """Get comprehensive status information"""
        with self.state_lock:
            return {
                'state': self.current_state.value,
                'is_ready': self.is_ready(),
                'is_initializing': self.is_initializing(),
                'has_error': self.has_error(),
                'last_error': str(self.last_error) if self.last_error else None,
                'initialization_duration': self.initialization_duration,
                'initialization_start_time': self.initialization_start_time
            }


class ModelReadyDecorator:
    """
    Decorator to wrap model initialization functions with ready events.
    Automatically manages state transitions.
    """
    
    def __init__(self, event_manager: ModelReadyEventManager):
        self.event_manager = event_manager
    
    def __call__(self, init_func: Callable):
        """Decorator that wraps initialization function"""
        def wrapper(*args, **kwargs):
            self.event_manager.start_initialization()
            
            try:
                result = init_func(*args, **kwargs)
                self.event_manager.mark_ready()
                return result
            except Exception as e:
                self.event_manager.mark_error(e)
                raise
        
        return wrapper


# Global event manager instance
_model_event_manager = None

def get_model_event_manager() -> ModelReadyEventManager:
    """Get global model event manager instance"""
    global _model_event_manager
    if _model_event_manager is None:
        _model_event_manager = ModelReadyEventManager()
    return _model_event_manager

def reset_model_event_manager():
    """Reset model event manager (for testing)"""
    global _model_event_manager
    _model_event_manager = None

def model_ready_decorator(init_func: Callable):
    """Convenience decorator for model initialization functions"""
    event_manager = get_model_event_manager()
    return ModelReadyDecorator(event_manager)(init_func)