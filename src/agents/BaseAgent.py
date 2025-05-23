from abc import ABC, abstractmethod

class BaseAgent(ABC):
    def __init__(self):
        self.history = []
    
    @abstractmethod
    def call(self, prompt: str):
        """Call the agent with a prompt and return the response.
        
        Args:
            prompt: The input prompt to send to the agent
            
        Returns:
            The agent's response
        """
        pass