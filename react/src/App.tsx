import { Routes, Route } from 'react-router-dom';
import Layout from './components/layouts/Default';
import ChatWindow from './components/chat/ChatWindow';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route path="chat" element={<ChatWindow />} />
        {/* Add other child routes here as needed */}
      </Route>
    </Routes>
  );
}

export default App;