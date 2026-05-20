import './styles/app.css';
import { Header } from './components/Header.jsx';
import { BankrollWidget } from './components/BankrollWidget.jsx';
import { SmartPredict } from './components/SmartPredict.jsx';


export default function App() {
  return (
    <div className="app">
      <Header />
      <BankrollWidget />
      <SmartPredict />
    </div>
  );
}
