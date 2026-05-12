import { AppProviders } from "./providers/AppProviders";
import { AppRouter } from "./router/AppRouter";
import "./styles/global.css";
import "@shared/ui/design-system.css";

function App() {
  return (
    <AppProviders>
      <AppRouter />
    </AppProviders>
  );
}

export default App;
