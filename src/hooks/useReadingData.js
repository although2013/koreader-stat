/* 读取 export_stats.py 生成的 reading_data.json */

import { useEffect, useState } from 'react';

const DATA_URL = './reading_data.json';

export function useReadingData() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(DATA_URL)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP 错误! 状态码: ${res.status}`);
        return res.json();
      })
      .then(jsonData => setData(jsonData))
      .catch(err => {
        console.error("加载数据失败:", err);
        setError(err.message);
      });
  }, []);

  return { data, error };
}
