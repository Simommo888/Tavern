import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Tavern AI 数字人直播工作台',
  description: '面向酒类品牌的 AI 数字人直播运营中台',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
