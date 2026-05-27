import { SpeakingPractice } from "@/components/speaking/SpeakingPractice";

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-blue-50 via-white to-white">
      {/* Top Nav Bar */}
      <nav className="border-b border-blue-100 bg-white/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-5xl mx-auto flex items-center justify-between px-6 py-3">
          <div className="flex items-center gap-2">
            <span className="text-2xl" role="img" aria-label="logo">🎓</span>
            <span className="text-lg font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
              VietSpeak AI
            </span>
          </div>
          <span className="text-xs text-gray-400">IELTS Speaking Evaluator</span>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="text-center pt-12 pb-6 px-4">
        <h1 className="text-4xl md:text-5xl font-extrabold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
          Luyện IELTS Speaking cùng AI
        </h1>
        <p className="text-gray-500 mt-3 max-w-xl mx-auto">
          Ghi âm câu trả lời của bạn — AI sẽ chấm điểm Lexical Resource &amp;
          Grammar theo chuẩn IELTS band 0–9, đồng thời sửa lỗi phát âm &amp;
          ngữ pháp.
        </p>
      </section>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 pb-16">
        <SpeakingPractice />
      </div>

      {/* Footer */}
      <footer className="text-center text-xs text-gray-400 pb-6">
        VietSpeak AI &copy; 2026 — Powered by Whisper &amp; LLaMA 3.1
      </footer>
    </main>
  );
}
