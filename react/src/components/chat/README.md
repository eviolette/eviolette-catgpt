# Chat Window Component

This project contains a React component called `ChatWindow`, which serves as an interactive chat interface. The component allows users to send messages in various formats and receive responses from an AI assistant.

## Features

- **Message Types**: Users can send messages in different formats:
  - Markdown
  - Python
  - README
  - JSON (with two schemas: BasicResponse and BasicListResponse)

- **Real-time Interaction**: The chat window updates in real-time, displaying both user and assistant messages.

- **Syntax Highlighting**: Messages are displayed with syntax highlighting based on their type using the `react-syntax-highlighter` library.

- **Error Handling**: If an error occurs while generating a response, an error message is displayed.

## Installation

To use this component, ensure you have the following dependencies installed:

```bash
npm install @mui/material @mui/icons-material axios react-syntax-highlighter
```

## Usage

1. **Import the Component**: You can import the `ChatWindow` component into your React application.

   ```tsx
   import ChatWindow from './ChatWindow';
   ```

2. **Render the Component**: Include the `ChatWindow` component in your JSX.

   ```tsx
   function App() {
       return (
           <div>
               <ChatWindow />
           </div>
       );
   }
   ```

3. **Backend Setup**: The component makes HTTP POST requests to a backend server running on `http://localhost:8081`. Ensure you have the appropriate endpoints set up to handle requests for each message type:
   - `/markdown`
   - `/python`
   - `/readme`
   - `/json`

   The backend should respond with a JSON object containing the `content` field for the assistant's reply.

## Component Structure

- **State Management**: The component uses React's `useState` to manage the following states:
  - `messages`: An array of chat messages.
  - `input`: The current input value from the user.
  - `expanded`: A boolean indicating if the input area is expanded.
  - `format`: The selected message format.

- **Message Rendering**: Each message is rendered using the `renderMessage` function, which applies different styles based on the message role (user or assistant) and type.

- **Scrolling**: The chat window automatically scrolls to the bottom when new messages are added.

## User Interaction

- **Input Area**: Users can type their messages in a text area. The input area expands when focused and collapses when blurred if empty.

- **Send Button**: Users can send their messages by clicking the send button, which triggers the `handleSend` function to process the input and fetch a response from the backend.

## Conclusion

The `ChatWindow` component provides a simple yet effective way to interact with an AI assistant through a chat interface. By following the setup instructions and ensuring the backend is properly configured, you can integrate this component into your React application.