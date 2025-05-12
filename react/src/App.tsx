import { Routes, Route } from 'react-router-dom';
import Layout from '../src/components/layouts/Default';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />} />
    </Routes>
  );
}

export default App;