import { Navigate, Route, Routes } from "react-router-dom";

import Layout from "@/components/Layout";
import AnalysisPage from "@/pages/AnalysisPage";
import ChatPage from "@/pages/ChatPage";
import LandingPage from "@/pages/LandingPage";
import NetworkPage from "@/pages/NetworkPage";
import RecommendationPage from "@/pages/RecommendationPage";
import SellPage from "@/pages/SellPage";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<LandingPage />} />
        <Route path="/sell" element={<SellPage />} />
        <Route path="/analysis/:listingId" element={<AnalysisPage />} />
        <Route path="/recommendation/:listingId" element={<RecommendationPage />} />
        <Route path="/network" element={<NetworkPage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
