type ClassValue = string | number | false | null | undefined | ClassValue[] | Record<string, boolean | undefined>;

export function cn(...values: ClassValue[]): string {
  const result: string[] = [];

  const append = (value: ClassValue): void => {
    if (!value) {
      return;
    }

    if (Array.isArray(value)) {
      value.forEach(append);
      return;
    }

    if (typeof value === "object") {
      Object.entries(value).forEach(([className, enabled]) => {
        if (enabled) {
          result.push(className);
        }
      });
      return;
    }

    result.push(String(value));
  };

  values.forEach(append);
  return result.join(" ");
}
