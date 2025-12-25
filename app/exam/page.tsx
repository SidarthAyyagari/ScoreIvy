'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import styles from './page.module.css'

interface Question {
  id: number
  question: string
  options: string[]
  correctAnswer: number
  explanation?: string
}

const questions: Question[] = [
  {
    id: 1,
    question: 'What is the capital of France?',
    options: ['London', 'Berlin', 'Paris', 'Madrid'],
    correctAnswer: 2,
    explanation: 'London is the capital of the United Kingdom, not France. Berlin is the capital of Germany. Madrid is the capital of Spain. Paris is the correct answer as it has been the capital of France since 987 AD and is the country\'s largest city, known as the "City of Light".'
  },
  {
    id: 2,
    question: 'Which planet is known as the Red Planet?',
    options: ['Venus', 'Mars', 'Jupiter', 'Saturn'],
    correctAnswer: 1,
    explanation: 'Venus is known as the "Morning Star" or "Evening Star" due to its brightness. Jupiter is the largest planet in our solar system. Saturn is famous for its rings. Mars is called the Red Planet because iron oxide (rust) on its surface gives it a distinctive reddish appearance, making it visible from Earth as a red object in the night sky.'
  },
  {
    id: 3,
    question: 'What is 2 + 2?',
    options: ['3', '4', '5', '6'],
    correctAnswer: 1,
    explanation: '3 is one less than 4, which is the result of 2 + 2. 5 is one more than 4. 6 is two more than 4. The correct answer is 4, as adding 2 and 2 together equals 4. This is a fundamental arithmetic operation in basic mathematics.'
  },
  {
    id: 4,
    question: 'Who wrote "Romeo and Juliet"?',
    options: ['Charles Dickens', 'William Shakespeare', 'Jane Austen', 'Mark Twain'],
    correctAnswer: 1,
    explanation: 'Charles Dickens wrote novels like "A Tale of Two Cities" and "Great Expectations". Jane Austen wrote "Pride and Prejudice" and "Sense and Sensibility". Mark Twain wrote "The Adventures of Tom Sawyer" and "Huckleberry Finn". William Shakespeare is the correct answer - he wrote "Romeo and Juliet" in the late 16th century, and it remains one of his most famous tragedies about two star-crossed lovers from feuding families.'
  },
  {
    id: 5,
    question: 'What is the largest ocean on Earth?',
    options: ['Atlantic Ocean', 'Indian Ocean', 'Arctic Ocean', 'Pacific Ocean'],
    correctAnswer: 3,
    explanation: 'The Atlantic Ocean is the second-largest ocean. The Indian Ocean is the third-largest. The Arctic Ocean is the smallest of the world\'s oceans. The Pacific Ocean is the correct answer - it is the largest and deepest ocean, covering approximately 63 million square miles (about one-third of Earth\'s surface) and containing more than half of the planet\'s free water.'
  },
  {
    id: 6,
    question: 'What is the chemical symbol for water?',
    options: ['H2O', 'CO2', 'O2', 'NaCl'],
    correctAnswer: 0,
    explanation: 'CO2 is carbon dioxide, a gas composed of one carbon and two oxygen atoms. O2 is molecular oxygen, the gas we breathe. NaCl is sodium chloride, commonly known as table salt. H2O is the correct answer - it represents water, with two hydrogen atoms bonded to one oxygen atom. Water is the most abundant compound on Earth\'s surface and essential for all known forms of life.'
  },
  {
    id: 7,
    question: 'Which year did World War II end?',
    options: ['1943', '1944', '1945', '1946'],
    correctAnswer: 2,
    explanation: '1943 and 1944 were years during the war, with major battles like D-Day occurring in 1944. 1946 was after the war had ended. 1945 is the correct answer - World War II ended in 1945. The war in Europe ended on May 8, 1945 (V-E Day), and the war in the Pacific ended on September 2, 1945 (V-J Day) after Japan surrendered following the atomic bombings of Hiroshima and Nagasaki.'
  },
  {
    id: 8,
    question: 'What is the smallest prime number?',
    options: ['0', '1', '2', '3'],
    correctAnswer: 2,
    explanation: '0 is not a prime number - it is neither prime nor composite. 1 is not considered a prime number because it only has one positive divisor (itself), and prime numbers must have exactly two distinct positive divisors. 3 is a prime number but not the smallest. 2 is the correct answer - it is the smallest prime number and the only even prime number, as it has exactly two positive divisors: 1 and 2.'
  },
  {
    id: 9,
    question: 'Which programming language is known as the "language of the web"?',
    options: ['Python', 'Java', 'JavaScript', 'C++'],
    correctAnswer: 2,
    explanation: 'Python is a versatile programming language used for data science, AI, and backend development. Java is used for enterprise applications and Android development. C++ is a systems programming language used for performance-critical applications. JavaScript is the correct answer - it is known as the "language of the web" because it is the primary scripting language that runs in web browsers, enabling interactive web pages and modern web applications. It\'s essential for front-end web development.'
  },
  {
    id: 10,
    question: 'What is the speed of light in vacuum (approximately)?',
    options: ['300,000 km/s', '150,000 km/s', '450,000 km/s', '600,000 km/s'],
    correctAnswer: 0,
    explanation: '150,000 km/s is half the speed of light. 450,000 km/s and 600,000 km/s are faster than the speed of light, which is impossible according to Einstein\'s theory of relativity. 300,000 km/s is the correct answer - the speed of light in a vacuum is approximately 299,792,458 meters per second, which rounds to about 300,000 km/s. This is a fundamental constant in physics, denoted by "c", and nothing can travel faster than this speed.'
  }
]

export default function ExamPage() {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null)
  const [answers, setAnswers] = useState<number[]>([])
  const router = useRouter()

  useEffect(() => {
    // Check if user is logged in
    const isLoggedIn = sessionStorage.getItem('isLoggedIn')
    if (!isLoggedIn) {
      router.push('/')
    }
  }, [router])

  const currentQuestion = questions[currentQuestionIndex]
  const isLastQuestion = currentQuestionIndex === questions.length - 1

  const handleAnswerSelect = (optionIndex: number) => {
    setSelectedAnswer(optionIndex)
  }

  const handleNext = () => {
    if (selectedAnswer === null) {
      alert('Please select an answer before proceeding')
      return
    }

    // Save the current answer
    const newAnswers = [...answers]
    newAnswers[currentQuestionIndex] = selectedAnswer
    setAnswers(newAnswers)

    if (isLastQuestion) {
      // Store results in sessionStorage and navigate to results
      sessionStorage.setItem('examAnswers', JSON.stringify(newAnswers))
      sessionStorage.setItem('examQuestions', JSON.stringify(questions))
      router.push('/results')
    } else {
      setCurrentQuestionIndex(currentQuestionIndex + 1)
      setSelectedAnswer(null)
    }
  }

  return (
    <div className={styles.container}>
      <div className={styles.examCard}>
        <div className={styles.header}>
          <div className={styles.progress}>
            Question {currentQuestionIndex + 1} of {questions.length}
          </div>
          <div className={styles.progressBar}>
            <div 
              className={styles.progressFill}
              style={{ width: `${((currentQuestionIndex + 1) / questions.length) * 100}%` }}
            />
          </div>
        </div>

        <div className={styles.questionSection}>
          <h2 className={styles.questionText}>{currentQuestion.question}</h2>
          
          <div className={styles.options}>
            {currentQuestion.options.map((option, index) => (
              <button
                key={index}
                onClick={() => handleAnswerSelect(index)}
                className={`${styles.option} ${
                  selectedAnswer === index ? styles.optionSelected : ''
                }`}
              >
                {option}
              </button>
            ))}
          </div>
        </div>

        <div className={styles.footer}>
          <button
            onClick={handleNext}
            className={styles.nextButton}
            disabled={selectedAnswer === null}
          >
            {isLastQuestion ? 'Finish Exam' : 'Next'}
          </button>
        </div>
      </div>
    </div>
  )
}

