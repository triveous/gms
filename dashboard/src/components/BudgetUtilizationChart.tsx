'use client'

import * as React from 'react'
import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from 'recharts'

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

const chartConfig = {
  forecasted: {
    label: 'Forecasted',
    color: '#00E396',
  },
  actual: {
    label: 'Actual',
    color: '#2E93FA',
  },
} satisfies ChartConfig

export interface BudgetUtilizationItem {
  quarter: string
  title: string
  quarterStartDate: string
  budgetSpent: number
  forecastedAmount: number
}

export function BudgetUtilizationChart({
  budgetUtilization,
}: {
  budgetUtilization: BudgetUtilizationItem[]
}) {
  const chartData = React.useMemo(() => {
    if (!budgetUtilization) return []
    return [...budgetUtilization]
      .sort((a, b) => new Date(a.quarterStartDate).getTime() - new Date(b.quarterStartDate).getTime())
      .map((item) => ({
        quarter: item.quarter,
        title: item.title,
        quarterStartDate: item.quarterStartDate,
        actual: item.budgetSpent / 10000000, // Convert to Crores
        forecasted: item.forecastedAmount / 10000000, // Convert to Crores
      }))
  }, [budgetUtilization])

  return (
    <div className="pt-0">
      <CardContent className="px-0 ">
        <ChartContainer
          config={chartConfig}
          className="aspect-auto h-[250px] w-full"
        >
          <AreaChart data={chartData} margin={{ left: 0, right: 0, top: 10, bottom: 0 }}>
            <defs>
              <linearGradient id="fillActual" x1="0" y1="0" x2="0" y2="1">
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
              <linearGradient id="fillForecasted" x1="0" y1="0" x2="0" y2="1">
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
            </defs>
            <CartesianGrid vertical={false} />
            <XAxis
              dataKey="quarter"
              tickLine={false}
              axisLine={false}
              tickMargin={10}
              tickFormatter={(value) => {
                 const parts = value.split('-')
                 if (parts.length >= 2) {
                    return `${parts[0]} ${parts[1]}`
                 }
                 return value
              }}
            />
             <YAxis
              hide={false}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => `${value}`}
             />
            <ChartTooltip
              cursor={false}
              content={
                <ChartTooltipContent
                  indicator="dot"
                  formatter={(value, name) => (
                      <div className="flex gap-2 text-xs">
                        <div 
                            className="w-3 h-3 rounded-[3px] shrink-0" 
                            style={{ 
                                backgroundColor: chartConfig[name as keyof typeof chartConfig]?.color 
                            }}
                        />
                        <span className="text-muted-foreground">{chartConfig[name as keyof typeof chartConfig]?.label || name}:</span>
                        <span className="font-bold">₹ {Number(value).toLocaleString('en-IN')} Cr.</span>
                      </div>
                  )}
                  labelFormatter={(value, payload) => {
                      if (payload && payload.length > 0) {
                          return payload[0].payload.title
                      }
                      return value
                  }}
                />
              }
            />
             <Area
              dataKey="actual"
              type="monotone"
              fill="url(#fillActual)"
              stroke="var(--color-actual)"
            />
            <Area
              dataKey="forecasted"
              type="monotone"
              fill="url(#fillForecasted)"
              stroke="var(--color-forecasted)"
            />
          </AreaChart>
        </ChartContainer>
      </CardContent>
    </div>
  )
}

