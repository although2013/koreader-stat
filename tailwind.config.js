/** @type {import('tailwindcss').Config} */
export default {
  // 只扫描这些文件里出现的类名 —— 因此代码里的类名必须是完整字面量，
  // 不能用 `bg-${color}-500` 这种拼接（现有组件都遵循了这一点）
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {},
  },
  plugins: [],
};
