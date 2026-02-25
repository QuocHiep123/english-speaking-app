import { SpeakingPractice } from "@/components/speaking/SpeakingPractice";

export default function Home() {
  return (
    <main className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <header className="text-center mb-12">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            VietSpeak AI
          </h1>
          <p className="text-gray-600 mt-2">
            Luyện phát âm tiếng Anh cùng AI
          </p>
        </header>

        {/* Main Speaking Practice Component */}
        <SpeakingPractice />
      </div>
    </main>
  );
}
