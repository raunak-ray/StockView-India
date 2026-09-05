# Alerts — how it works

This page walks through the form state, the create flow, the two alert
lists (Watching and Triggered), the clear flows, and the known bug in
the backend's market-data lookup.

## The big picture

```mermaid
flowchart TD
    Page[AlertsPage] --> Hook[useAlerts - query]
    Page --> Create[useCreateAlert - mutation]
    Page --> Delete[useDeleteAlert - mutation]
    Page --> Clear[useClearAlerts - mutation]
    Page --> Form[Create form]
    Form --> Symbol[SymbolSearch]
    Form --> Price[Price input]
    Form --> Cond[Condition select]
    Page --> Watch[Watching list]
    Page --> Fired[Triggered list]
    Hook -->|GET /alerts| BE
    Create -->|POST /alerts| BE
    Delete -->|DELETE /alerts/{id}| BE
    Clear -->|DELETE /alerts?fired_only=true or ''| BE
    BE --> Mem[In-memory per-user alerts dict]
    BE --> Polling[Background polling - every 30s]
    Polling --> MD[market_data quote - BROKEN: looks for lastPrice]
```

Four backend endpoints. The form state is local to the page. The
"Watching" and "Triggered" lists come from the same query but are
split by the `triggered` flag.

## The page state

```typescript
const [symbol, setSymbol] = useState("RELIANCE.NS");
const [price, setPrice] = useState("");
const [condition, setCondition] = useState("above");
```

Three fields. Defaults: RELIANCE.NS symbol, empty price, "above"
condition.

## The form

```tsx
<Card>
  <CardHeader className="pb-4">
    <CardTitle className="flex items-center gap-2 text-sm">
      <Bell className="size-4 text-gold" />Set alert
    </CardTitle>
  </CardHeader>
  <CardContent className="space-y-4">
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
      <div className="space-y-1.5">
        <Label className="text-xs">Symbol</Label>
        <SymbolSearch value={symbol} onChange={(t) => setSymbol(t)} placeholder="Search stock…" />
      </div>
      <div className="space-y-1.5">
        <Label className="text-xs">Price (₹)</Label>
        <Input type="number" min={0.01} step={0.5} value={price} onChange={(e) => setPrice(e.target.value)} className="font-mono text-sm" placeholder="2800.00" />
      </div>
      <div className="space-y-1.5">
        <Label className="text-xs">Condition</Label>
        <Select value={condition} onValueChange={setCondition}>
          <SelectTrigger className="w-full font-mono text-sm"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="above">Crosses Above</SelectItem>
            <SelectItem value="below">Crosses Below</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
    <Button onClick={handleCreate} disabled={createAlert.isPending || !symbol.trim() || !price} className="w-full bg-gold text-gold-foreground hover:bg-gold/90 sm:w-auto">
      <Plus className="mr-1 size-4" />Add Alert
    </Button>
  </CardContent>
</Card>
```

The form is a 3-column grid on `sm` and up, single column on mobile.
The submit button is full-width on mobile, auto-width on desktop.
The colour is gold (the "alert" theme colour).

## The submit handler

```typescript
const handleCreate = () => {
  if (!symbol.trim() || !price) return;
  createAlert.mutate(
    {
      symbol: symbol.trim().toUpperCase(),
      price: Number(price),
      condition,
      label: condition === "above" ? "Crosses Above" : "Crosses Below",
    },
    { onSuccess: () => setPrice("") },
  );
};
```

The handler validates the symbol and price, then fires the mutation
with a derived `label` field. On success, the price field is cleared
(so the user can quickly set another alert on the same symbol).

The toast notification (from `useCreateAlert`'s `onSuccess`) shows:
"Alert created: RELIANCE.NS above ₹2,800".

## The two alert lists

The `useAlerts` hook returns:

```typescript
{ active: Alert[], fired: Alert[], triggered_now: Alert[] }
```

The page uses `active` and `fired`. The `triggered_now` field is
populated by the backend when alerts were just fired by the polling
loop — the frontend doesn't use it directly, but it's available for
toast popups or badges.

### The Watching list

```tsx
{!isLoading && active.length > 0 && (
  <div className="space-y-2">
    <div className="flex items-center justify-between">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Watching ({active.length})</h2>
      <Button variant="ghost" size="sm" className="h-7 text-xs text-muted-foreground" onClick={() => clearAlerts.mutate(false)} disabled={clearAlerts.isPending}>
        <Trash2 className="mr-1 size-3" />Clear all
      </Button>
    </div>
    {active.map((a) => (
      <div key={a.id} className="flex items-center justify-between rounded-xl border border-border bg-card px-4 py-3">
        <div className="flex items-center gap-4">
          <Bell className="size-4 text-gold" />
          <span className="font-mono text-sm font-bold">{a.symbol}</span>
          <span className={cn("rounded-full px-2 py-0.5 text-[10px] font-semibold", a.condition === "above" ? "bg-up/10 text-up" : "bg-down/10 text-down")}>
            {a.condition === "above" ? "ABOVE" : "BELOW"}
          </span>
          <span className="font-mono text-base font-bold text-gold">₹{a.price.toLocaleString("en-IN")}</span>
          <span className="text-[10px] text-muted-foreground">Set {a.created}</span>
        </div>
        <Button variant="ghost" size="sm" className="size-8 p-0 text-muted-foreground hover:text-down" onClick={() => deleteAlert.mutate(a.id)} disabled={deleteAlert.isPending}>
          <X className="size-4" />
        </Button>
      </div>
    ))}
  </div>
)}
```

Each row has:
- A gold bell icon.
- The symbol (mono, bold).
- A condition pill (ABOVE/BELOW) — green for above, red for below.
- The price (mono, bold, gold).
- The set timestamp.
- A delete button (X) on the right.

The row has a normal border and white background — the active state.

### The Triggered list

```tsx
{!isLoading && fired.length > 0 && (
  <div className="space-y-2">
    <div className="flex items-center justify-between">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-down">Triggered ({fired.length})</h2>
      <Button variant="ghost" size="sm" className="h-7 text-xs text-muted-foreground" onClick={() => clearAlerts.mutate(true)} disabled={clearAlerts.isPending}>
        <Trash2 className="mr-1 size-3" />Clear triggered
      </Button>
    </div>
    {fired.map((a) => (
      <div key={a.id} className="flex items-center justify-between rounded-xl border border-down/20 bg-down/5 px-4 py-3">
        <div className="flex items-center gap-4">
          <BellOff className="size-4 text-down" />
          ...
        </div>
        <Button variant="ghost" size="sm" className="size-8 p-0 text-muted-foreground hover:text-down" onClick={() => deleteAlert.mutate(a.id)} disabled={deleteAlert.isPending}>
          <X className="size-4" />
        </Button>
      </div>
    ))}
  </div>
)}
```

The triggered rows have:
- A red `BellOff` icon (struck-out bell).
- A red border (`border-down/20`) and red-tinted background (`bg-down/5`).
- A red "Triggered (N)" header.

The `clearAlerts(true)` call passes `firedOnly=true` to the backend,
which only clears the fired list.

## The clear flows

```typescript
// Clear all (active + fired)
clearAlerts.mutate(false);

// Clear fired only
clearAlerts.mutate(true);
```

The `useClearAlerts` hook calls the api's `clearAlerts(firedOnly)`:

```typescript
export async function clearAlerts(firedOnly = false): Promise<void> {
  const qs = firedOnly ? "?fired_only=true" : "";
  return api.del<void>(`/alerts${qs}`);
}
```

The backend accepts a `fired_only` query param. With `?fired_only=true`,
only the fired list is cleared. Without it, all alerts (active + fired)
are cleared.

## The known bug (alerts `lastPrice` vs `price`)

The backend's alert evaluation loop iterates over the user's active
alerts and looks up the live price. The lookup uses the wrong key:

```python
# In backend/app/modules/alerts/service.py
quote = await market_data.get_quote(alert.symbol)
last = quote.get("lastPrice", alert.price)  # <-- BUG: "lastPrice" should be "price"
```

The market-data endpoint returns `{ price, change, change_pct, ... }`
— the key is `price`, not `lastPrice`. The `quote.get("lastPrice", ...)`
returns `alert.price` (the alert's stored price), so the comparison
is always `alert.condition (alert.price, alert.price)` — which always
triggers an "above" alert and never triggers a "below" alert.

### The exact failure

For an alert with `condition="above"`, `price=2800`:
- `last = quote.get("lastPrice", 2800)` → `last = 2800` (fallback).
- `last >= alert.price` → `2800 >= 2800` → `True`.
- Alert is marked as fired.

For an alert with `condition="below"`, `price=1400`:
- `last = quote.get("lastPrice", 1400)` → `last = 1400`.
- `last <= alert.price` → `1400 <= 1400` → `True`.
- Alert is marked as fired.

So every active alert fires immediately on the next polling cycle. The
"Watching" list is always empty shortly after creation.

### The fix

A 4-line change in `backend/app/modules/alerts/service.py`:

```python
quote = await market_data.get_quote(alert.symbol)
if quote is None:
    continue
last = quote.get("price")  # was: quote.get("lastPrice", alert.price)
if last is None:
    continue
if alert.condition == "above" and last >= alert.price:
    alert.triggered = True
elif alert.condition == "below" and last <= alert.price:
    alert.triggered = True
```

The fix:
1. Skip alerts whose quote fetch failed.
2. Read the correct key (`price`, not `lastPrice`).
3. Skip alerts with a None price.
4. Apply the condition check.

### Impact

Until the fix is applied:
- Every active alert fires within one polling cycle (30s by default).
- The "Watching" list is effectively empty (alerts move to "Triggered"
  on the next list call).
- The "Triggered" list shows all alerts ever created (until cleared).
- The alert system is unusable.

This is a high-priority bug. It should be fixed before any demo or
production use.

## What can go wrong

| Symptom | Cause |
|---|---|
| Add Alert button is greyed out | Symbol is empty or price is empty. |
| Alert created but immediately moves to Triggered | **The `lastPrice` bug.** The fix is in the implementation file. |
| Watching list is always empty | Same bug. |
| No notification when alert fires | The page does not push notifications. Navigate to the page to see fired alerts. |
| Alert is missing after server restart | The alert store is in-memory. Server restart wipes the data. |
| Symbol is invalid | The SymbolSearch rejects non-NSE symbols. Pick a valid one. |
| Condition is empty | The condition is always "above" or "below" — defaults to "above". |
| Price is 0 or negative | The `min={0.01}` prevents this. |

Related: [implementation](implementation.md) for the file map and the
bug fix details.