import { mount } from '@vue/test-utils'
import App from '@/App.vue'
import axios from 'axios'

jest.mock('axios')

describe('App.vue', () => {
  let wrapper

  beforeEach(() => {
    wrapper = mount(App)
  })

  it('renders correctly', () => {
    expect(wrapper.find('h1').text()).toBe('Dialog chat bot')
    expect(wrapper.find('input').exists()).toBe(true)
    expect(wrapper.find('button').text()).toBe('Send')
  })

  it('disables send button when input is empty', async () => {
    await wrapper.setData({ message: '' })
    expect(wrapper.find('button').attributes('disabled')).toBeDefined()
  })

  it('enables send button when input is not empty', async () => {
    await wrapper.setData({ message: 'Hello' })
    expect(wrapper.find('button').attributes('disabled')).toBeUndefined()
  })

  it('adds user message to messages array', async () => {
    await wrapper.setData({ message: 'Hello' })
    await wrapper.find('button').trigger('click')
    expect(wrapper.vm.messages).toContainEqual({ text: 'Hello', type: 'user' })
  })

  it('calls API and adds response to messages', async () => {
    axios.post.mockResolvedValue({ data: 'API response' })
    await wrapper.setData({ message: 'Hello' })
    await wrapper.find('button').trigger('click')
    expect(axios.post).toHaveBeenCalledWith('http://192.168.1.32:8080/chat', { message: 'Hello' })
    await wrapper.vm.$nextTick()
    expect(wrapper.vm.messages).toContainEqual({ text: 'API response', type: 'api' })
  })

  it('switches API on network error', async () => {
    axios.post.mockRejectedValue({ code: 'ERR_NETWORK' })
    axios.get.mockResolvedValue({}) // Simuler une réponse réussie pour checkPreviousApi
    await wrapper.setData({ message: 'Hello' })
    await wrapper.find('button').trigger('click')
    await wrapper.vm.$nextTick()
    expect(wrapper.vm.currentApiUrl).toBe('http://192.168.1.32:8090')
    expect(wrapper.vm.messages).toContainEqual({ text: 'Basculement vers une autre API, veuillez réessayer.', type: 'system' })
  })

  it('handles invalid message', async () => {
    axios.post.mockRejectedValue({ response: { status: 400 } })
    await wrapper.setData({ message: 'Invalid' })
    await wrapper.find('button').trigger('click')
    await wrapper.vm.$nextTick()
    expect(wrapper.vm.messages).toContainEqual({ text: 'Message non valide, recommencez', type: 'error' })
  })

  it('checks previous API with exponential backoff', async () => {
    jest.useFakeTimers()
    axios.get.mockRejectedValueOnce({}).mockResolvedValueOnce({})
    const checkPreviousApiSpy = jest.spyOn(wrapper.vm, 'checkPreviousApi')
    
    wrapper.vm.checkPreviousApi()
    
    jest.advanceTimersByTime(1000) // Premier délai
    await wrapper.vm.$nextTick()
    jest.advanceTimersByTime(2000) // Deuxième délai
    await wrapper.vm.$nextTick()
    
    expect(checkPreviousApiSpy).toHaveBeenCalled()
    expect(axios.get).toHaveBeenCalledTimes(2)
    
    jest.useRealTimers()
  })
})
