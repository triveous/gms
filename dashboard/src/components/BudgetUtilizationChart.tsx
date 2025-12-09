'use client'

import * as React from 'react'
import { Area, AreaChart, CartesianGrid, XAxis } from 'recharts'

import {
  CardContent,
} from '@/components/ui/card'
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from '@/components/ui/chart'

export const description = 'An interactive area chart'

const chartData = [
  { date: '2024-04-01', forcasted: 55, actual: 40 },
  { date: '2024-04-02', forcasted: 25, actual: 45 },
  { date: '2024-04-03', forcasted: 42, actual: 30 },
  { date: '2024-04-04', forcasted: 60, actual: 65 },
  { date: '2024-04-05', forcasted: 93, actual: 73 },
  { date: '2024-04-06', forcasted: 75, actual: 85 },
  { date: '2024-04-07', forcasted: 61, actual: 45 },
  { date: '2024-04-08', forcasted: 100, actual: 80 },
  { date: '2024-04-09', forcasted: 15, actual: 28 },
  { date: '2024-04-10', forcasted: 65, actual: 48 },
  { date: '2024-04-11', forcasted: 82, actual: 88 },
  { date: '2024-04-12', forcasted: 73, actual: 53 },
  { date: '2024-04-13', forcasted: 86, actual: 95 },
  { date: '2024-04-14', forcasted: 34, actual: 55 },
]

const chartConfig = {
  visitors: {
    label: 'Visitors',
  },
  forcasted: {
    label: 'Forcasted',
    color: '#00E396',
  },
  actual: {
    label: 'Actual',
    color: '#2E93FA',
  },
} satisfies ChartConfig

export function BudgetUtilizationChart() {
  const [timeRange] = React.useState('90d')

  const filteredData = chartData.filter((item) => {
    const date = new Date(item.date)
    const referenceDate = new Date('2024-06-30')
    let daysToSubtract = 90
    if (timeRange === '30d') {
      daysToSubtract = 30
    } else if (timeRange === '7d') {
      daysToSubtract = 7
    }
    const startDate = new Date(referenceDate)
    startDate.setDate(startDate.getDate() - daysToSubtract)
    return date >= startDate
  })

  return (
    <div className="pt-0">
      <CardContent className="px-2 pt-4 sm:px-6 sm:pt-6">
        <ChartContainer
          config={chartConfig}
          className="aspect-auto h-[250px] w-full"
        >
          <AreaChart data={filteredData}>
            <defs>
              <linearGradient id="fillActual" x1="0" y1="0" x2="0" y2="1">
                <stop
                  offset="5%"
                  stopColor="#00E396"
                  stopOpacity={0.8}
                />
                <stop
                  offset="95%"
                  stopColor="#00E396"
                  stopOpacity={0.1}
                />
              </linearGradient>
              <linearGradient id="fillForcasted" x1="0" y1="0" x2="0" y2="1">
                <stop
                  offset="5%"
                  stopColor="#2E93FA"
                  stopOpacity={0.8}
                />
                <stop
                  offset="95%"
                  stopColor="#2E93FA"
                  stopOpacity={0.1}
                />
              </linearGradient>
            </defs>
            <CartesianGrid vertical={false} />
            <XAxis
              dataKey="date"
              tickLine={false}
              axisLine={false}
              tickMargin={8}
              minTickGap={32}
              tickFormatter={(value) => {
                const date = new Date(value)
                return date.toLocaleDateString('en-US', {
                  month: 'short',
                  day: 'numeric',
                })
              }}
            />
            <ChartTooltip
              cursor={false}
              content={
                <ChartTooltipContent
                  labelFormatter={(value) => {
                    return new Date(value).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                    })
                  }}
                  indicator="dot"
                />
              }
            />
            <Area
              dataKey="forcasted"
              type="natural"
              fill="url(#fillForcasted)"
              stroke="var(--color-actual)"
              stackId="a"
            />
            <Area
              dataKey="actual"
              type="natural"
              fill="url(#fillActual)"
              stroke="var(--color-forcasted)"
              stackId="a"
            />
          </AreaChart>
        </ChartContainer>
      </CardContent>
    </div>
  )
}
