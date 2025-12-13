import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { TicketsPage } from '@/pages/TicketsPage'
import { Toaster } from '@/components/ui/toaster'
import './App.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TicketsPage />
      <Toaster />
    </QueryClientProvider>
  )
}

export default App
