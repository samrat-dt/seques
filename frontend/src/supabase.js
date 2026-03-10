import { createClient } from '@supabase/supabase-js'

const url = import.meta.env.VITE_SUPABASE_URL || 'https://deekxushpzcxmzdcvfxq.supabase.co'
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRlZWt4dXNocHpjeG16ZGN2ZnhxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzI4OTY2NzUsImV4cCI6MjA4ODQ3MjY3NX0.FTgQHXiaZQJo5UyGx4pW4QvLQJCM_89Se55QHg_eoOA'

export const supabase = createClient(url, anonKey)
