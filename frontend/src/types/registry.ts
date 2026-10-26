export type JsonValue =
  | string
  | number
  | boolean
  | null
  | JsonValue[]
  | { [key: string]: JsonValue };

export interface RegistryOption {
  id: string;
  group: string;
  group_label: string;
  applies_to: string[];
  type:
    | 'number'
    | 'integer'
    | 'boolean'
    | 'string'
    | 'select'
    | 'markers'
    | 'list'
    | 'object';
  default: JsonValue;
  path: string[];
  ui: {
    control: string;
    label: string;
    tab: string;
    order: number;
    section?: string;
    options?: { value: string; label: string }[];
  };
  rationale: string;
  source: string;
  unit: string | null;
  allowed_units: string[];
  min: number | null;
  max: number | null;
  step: number | null;
  enum: string[];
  depends_on: string[];
  nullable: boolean;
  required?: boolean;
  enum_labels?: [string, string][];
  fields?: RegistryOption[];
  item_fields?: RegistryOption[];
  item_variants?: [string, string[]][];
}

export interface RegistrySchema {
  schema_version: number;
  groups: { id: string; label: string }[];
  options: RegistryOption[];
}

export interface ProfileOptions {
  schema_version: number;
  source: 'jsonb' | 'legacy';
  values: Record<string, JsonValue>;
}
